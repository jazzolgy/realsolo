"""Product-facing facade for the combined AI Transcription + Notation engine.

The commercial product is one continuous pipeline:
source evidence -> transcription interpretation -> notation candidates ->
logical score -> engraving/export.

Audio decoding/model inference is intentionally outside this module for now.
Source adapters must convert their output into versioned Performance Evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .allocation import (
    AllocationEvidence,
    StaffProfile,
    VoiceStaffCandidate,
    allocation_candidates,
)
from .engraving import EngravingPlan, EngravingProfile, build_default_engraving_plan
from .events import CommittedPerformanceEvent
from .musicxml import score_to_musicxml
from .notation import (
    NotatedAtomKind,
    NotationCandidate,
    NotationIntent,
    choose_preferred_candidate,
)
from .pipeline import basic_rhythm_candidates, notation_intent_from_event
from .quality import ScoreQualityReport, audit_score_for_performance
from .score import LogicalScore, LogicalScorePart, ScoreEvent, assemble_logical_score
from .spelling import (
    PitchSpellingCandidate,
    PitchSpellingContext,
    spelling_candidates,
)


class PerformanceEvidenceSource(Protocol):
    """Adapter boundary for audio, MIDI, upload, or embedded RealSolo sources."""

    def performance_events(self) -> Sequence[CommittedPerformanceEvent]:
        ...


@dataclass(frozen=True)
class TranscriptionNotationConfig:
    meter_numerator: int = 4
    meter_denominator: int = 4
    fidelity_weight: float = 1.0
    readability_weight: float = 1.0
    complexity_weight: float = 1.0
    engraving_profile: EngravingProfile = EngravingProfile()

    def validate(self) -> None:
        if self.meter_numerator <= 0 or self.meter_denominator <= 0:
            raise ValueError("meter must be positive")
        for value, name in (
            (self.fidelity_weight, "fidelity_weight"),
            (self.readability_weight, "readability_weight"),
            (self.complexity_weight, "complexity_weight"),
        ):
            if value < 0:
                raise ValueError(f"{name} may not be negative")
        self.engraving_profile.validate()


@dataclass(frozen=True)
class EventTranscriptionResult:
    source_event: CommittedPerformanceEvent
    event_id: str
    intent: NotationIntent
    rhythm_candidates: tuple[NotationCandidate, ...]
    preferred_rhythm: NotationCandidate
    spelling_candidates: tuple[PitchSpellingCandidate, ...] = ()
    allocation_candidates: tuple[VoiceStaffCandidate, ...] = ()


class TranscriptionNotationEngine:
    """Stable product-facing API shared by RealSolo and a future standalone app."""

    def __init__(
        self,
        config: TranscriptionNotationConfig = TranscriptionNotationConfig(),
    ):
        config.validate()
        self.config = config

    def transcribe_event(
        self,
        event: CommittedPerformanceEvent,
        *,
        spelling_context: PitchSpellingContext = PitchSpellingContext(),
        staffs: tuple[StaffProfile, ...] = (),
        previous_staff_id: str | None = None,
        preferred_staff_id: str | None = None,
    ) -> EventTranscriptionResult:
        event.validate()
        intent = notation_intent_from_event(event)
        rhythm_candidates = basic_rhythm_candidates(
            event,
            intent,
            meter_numerator=self.config.meter_numerator,
            meter_denominator=self.config.meter_denominator,
        )
        if not rhythm_candidates:
            raise ValueError("event produced no notation candidates")

        preferred_rhythm = choose_preferred_candidate(
            rhythm_candidates,
            fidelity_weight=self.config.fidelity_weight,
            readability_weight=self.config.readability_weight,
            complexity_weight=self.config.complexity_weight,
        )

        pitch_candidates: tuple[PitchSpellingCandidate, ...] = ()
        if event.pitch is not None and event.pitch.nominal_midi is not None:
            pitch_candidates = spelling_candidates(event.pitch, spelling_context)

        staff_candidates: tuple[VoiceStaffCandidate, ...] = ()
        if staffs:
            staff_candidates = allocation_candidates(
                AllocationEvidence(
                    source_event_ids=(event.event_id,),
                    nominal_midi=(
                        event.pitch.nominal_midi
                        if event.pitch is not None
                        else None
                    ),
                    voice_role=event.voice_role,
                    layer_role=event.layer_role,
                    previous_staff_id=previous_staff_id,
                    preferred_staff_id=preferred_staff_id,
                ),
                staffs,
            )

        return EventTranscriptionResult(
            source_event=event,
            event_id=event.event_id,
            intent=intent,
            rhythm_candidates=rhythm_candidates,
            preferred_rhythm=preferred_rhythm,
            spelling_candidates=pitch_candidates,
            allocation_candidates=staff_candidates,
        )

    def transcribe_source(
        self,
        source: PerformanceEvidenceSource,
        *,
        spelling_context: PitchSpellingContext = PitchSpellingContext(),
        staffs: tuple[StaffProfile, ...] = (),
    ) -> tuple[EventTranscriptionResult, ...]:
        return tuple(
            self.transcribe_event(
                event,
                spelling_context=spelling_context,
                staffs=staffs,
            )
            for event in source.performance_events()
        )

    def logical_score_for_part(
        self,
        results: Sequence[EventTranscriptionResult],
        *,
        score_id: str,
        title: str,
        part_id: str,
        part_name: str,
        instrument: str,
        staff_ids: tuple[str, ...],
        profile_id: str | None = None,
    ) -> LogicalScore:
        """Assemble chosen transcription results into a renderer-neutral score.

        This is intentionally one-part first. Multi-part orchestration can build
        multiple LogicalScoreParts with the same event projection rule without
        coupling the core engine to any product UI.
        """

        if not results:
            raise ValueError("at least one transcription result is required")
        if not staff_ids:
            raise ValueError("at least one staff_id is required")

        score_events: list[ScoreEvent] = []
        for result in results:
            source = result.source_event
            allocation = (
                result.allocation_candidates[0]
                if result.allocation_candidates
                else None
            )
            staff_id = allocation.staff_id if allocation else staff_ids[0]
            voice_id = allocation.voice_id if allocation else f"{staff_id}:voice"

            preferred_pitch = (
                result.spelling_candidates[0].written_pitch
                if result.spelling_candidates
                else None
            )

            for index, atom in enumerate(result.preferred_rhythm.atoms):
                is_rest = atom.kind is NotatedAtomKind.REST
                score_events.append(
                    ScoreEvent(
                        event_id=f"score:{result.event_id}:{index}",
                        part_id=part_id,
                        staff_id=staff_id,
                        voice_id=voice_id,
                        kind=atom.kind,
                        span=atom.span,
                        source_event_ids=() if is_rest else atom.source_event_ids,
                        written_pitch=(
                            None
                            if is_rest or source.unpitched is not None
                            else preferred_pitch
                        ),
                        unpitched=(
                            source.unpitched
                            if not is_rest and source.unpitched is not None
                            else None
                        ),
                        tie_from_previous=atom.tie_from_previous,
                        tie_to_next=atom.tie_to_next,
                        tuplet=atom.tuplet,
                        articulations=source.articulation,
                        markings=source.ornament + source.technique,
                        confidence=result.intent.confidence,
                        provenance=source.provenance + ("transcribe:logical-score-projection",),
                    )
                )

        score_events.sort(key=lambda e: (e.span.onset, e.staff_id, e.voice_id, e.event_id))
        part = LogicalScorePart(
            part_id=part_id,
            name=part_name,
            instrument=instrument,
            staff_ids=staff_ids,
            events=tuple(score_events),
            profile_id=profile_id,
        )
        return assemble_logical_score(
            score_id=score_id,
            title=title,
            parts=(part,),
            meter_numerator=self.config.meter_numerator,
            meter_denominator=self.config.meter_denominator,
            provenance=("transcription-notation-product",),
        )

    def engraving_plan(self, score: LogicalScore) -> EngravingPlan:
        return build_default_engraving_plan(
            score,
            profile=self.config.engraving_profile,
        )

    def audit(self, score: LogicalScore) -> ScoreQualityReport:
        return audit_score_for_performance(score)

    def musicxml(
        self,
        score: LogicalScore,
        *,
        engraving_plan: EngravingPlan | None = None,
    ) -> str:
        plan = engraving_plan or self.engraving_plan(score)
        return score_to_musicxml(score, plan)
