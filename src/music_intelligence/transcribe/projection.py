"""End-to-end event projection for the initial transcription vertical slice."""
from __future__ import annotations

from dataclasses import dataclass

from .allocation import (
    AllocationEvidence,
    StaffProfile,
    VoiceStaffCandidate,
    allocation_candidates,
)
from .events import CommittedPerformanceEvent
from .instrument_rules import InstrumentNotationDirective
from .instrument_profiles import TranspositionSpec
from .notation import (
    NotationCandidate,
    NotationIntent,
    RhythmNotationContext,
    choose_preferred_candidate,
)
from .pipeline import basic_rhythm_candidates, notation_intent_from_event
from .score import ScoreEvent
from .spelling import (
    PitchSpellingCandidate,
    PitchSpellingContext,
    spelling_candidates,
)


def dynamic_marking_from_level(level: float | None) -> str | None:
    """Convert normalized performed loudness intent to a readable dynamic.

    This is deliberately coarse: the score should communicate an actionable
    dynamic level rather than encode continuous amplitude as notation.
    """

    if level is None:
        return None
    if not 0.0 <= level <= 1.0:
        raise ValueError("dynamic level must be within 0..1")
    if level < .15:
        return "pp"
    if level < .30:
        return "p"
    if level < .45:
        return "mp"
    if level < .62:
        return "mf"
    if level < .82:
        return "f"
    return "ff"


@dataclass(frozen=True)
class EventProjectionResult:
    intent: NotationIntent
    rhythm_candidates: tuple[NotationCandidate, ...]
    preferred_rhythm: NotationCandidate
    spelling_candidates: tuple[PitchSpellingCandidate, ...]
    allocation_candidates: tuple[VoiceStaffCandidate, ...]
    score_events: tuple[ScoreEvent, ...]


def project_pitched_event(
    event: CommittedPerformanceEvent,
    *,
    part_id: str,
    staffs: tuple[StaffProfile, ...],
    spelling_context: PitchSpellingContext = PitchSpellingContext(),
    directive: InstrumentNotationDirective | None = None,
    transposition: TranspositionSpec = TranspositionSpec(),
    meter_numerator: int = 4,
    meter_denominator: int = 4,
    rhythm_context: RhythmNotationContext = RhythmNotationContext(),
    previous_staff_id: str | None = None,
) -> EventProjectionResult:
    """Project one committed pitched event into score-domain events.

    All competing rhythm/spelling/allocation candidates are returned alongside
    the preferred projection so later evaluation or human correction can inspect
    alternatives.
    """

    event.validate()
    if event.pitch is None:
        raise ValueError("project_pitched_event requires pitched event")

    intent = notation_intent_from_event(
        event,
        relevance=directive.relevance if directive is not None else None,
    ) if directive is not None else notation_intent_from_event(event)

    rhythms = basic_rhythm_candidates(
        event,
        intent,
        meter_numerator=meter_numerator,
        meter_denominator=meter_denominator,
        rhythm_context=rhythm_context,
    )
    if not rhythms:
        raise ValueError("event notation intent produced no score candidate")
    preferred_rhythm = choose_preferred_candidate(rhythms)

    # Performance evidence is sounding pitch; notation for a transposing
    # instrument must be spelled at written pitch.  MusicXML's transpose
    # element separately tells playback/renderers how written pitch sounds.
    written_offset = -transposition.chromatic_semitones - 12 * transposition.octave_change
    spelling_pitch = event.pitch
    if written_offset:
        spelling_pitch = type(event.pitch)(
            nominal_midi=event.pitch.nominal_midi + written_offset,
            frequency_hz=event.pitch.frequency_hz,
            cents_offset=event.pitch.cents_offset,
            continuous_pitch_ref=event.pitch.continuous_pitch_ref,
        )
    spellings = spelling_candidates(spelling_pitch, spelling_context)
    preferred_pitch = spellings[0]

    allocations = allocation_candidates(
        AllocationEvidence(
            source_event_ids=(event.event_id,),
            nominal_midi=event.pitch.nominal_midi,
            voice_role=event.voice_role,
            layer_role=event.layer_role,
            previous_staff_id=previous_staff_id,
        ),
        staffs,
    )
    preferred_allocation = allocations[0]

    markings = directive.markings if directive is not None else ()
    articulations = (
        directive.articulations
        if directive is not None and directive.articulations
        else event.articulation
    )

    score_events = tuple(
        ScoreEvent(
            event_id=f"score:{event.event_id}:{index}",
            part_id=part_id,
            staff_id=preferred_allocation.staff_id,
            voice_id=preferred_allocation.voice_id,
            kind=atom.kind,
            span=atom.span,
            source_event_ids=atom.source_event_ids,
            written_pitch=preferred_pitch.written_pitch,
            tie_from_previous=atom.tie_from_previous,
            tie_to_next=atom.tie_to_next,
            tuplet=atom.tuplet,
            dynamic_marking=dynamic_marking_from_level(event.dynamics.dynamic_absolute_ordinal if event.dynamics is not None and event.dynamics.dynamic_absolute_ordinal is not None else event.dynamic),
            musical_coordinate=event.musical_coordinate,
            dynamics=event.dynamics,
            articulations=articulations,
            markings=markings,
            confidence=preferred_rhythm.confidence,
            provenance=preferred_rhythm.provenance + ("transcribe:event-projection",),
        )
        for index, atom in enumerate(preferred_rhythm.atoms)
    )
    for score_event in score_events:
        score_event.validate()

    return EventProjectionResult(
        intent=intent,
        rhythm_candidates=rhythms,
        preferred_rhythm=preferred_rhythm,
        spelling_candidates=spellings,
        allocation_candidates=allocations,
        score_events=score_events,
    )
