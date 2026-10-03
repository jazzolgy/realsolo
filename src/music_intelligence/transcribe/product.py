"""Product-facing facade for the combined AI Transcription + Notation engine.

The commercial product is one continuous pipeline:
source evidence -> transcription interpretation -> notation candidates -> score.

Audio decoding/model inference is intentionally outside this module for now.
Source adapters must convert their output into versioned Performance Evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Protocol, Sequence

from .allocation import (
    AllocationEvidence,
    StaffProfile,
    VoiceStaffCandidate,
    allocation_candidates,
)
from .events import CommittedPerformanceEvent
from .notation import (
    NotationCandidate,
    NotationIntent,
    choose_preferred_candidate,
)
from .pipeline import basic_rhythm_candidates, notation_intent_from_event
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


@dataclass(frozen=True)
class EventTranscriptionResult:
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
