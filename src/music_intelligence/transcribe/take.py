"""Batch transcription vertical slice from Performance Evidence to LogicalScore.

This module intentionally consumes only the transcription-side committed
performance contract.  It has no dependency on Audio Evidence Engine internals.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .allocation import StaffProfile
from .events import CommittedPerformanceEvent
from .instrument_profiles import TranspositionSpec, resolve_instrument_profile
from .instrument_rules import InstrumentNotationDirective
from .projection import EventProjectionResult, project_pitched_event
from .score import ReadableScore, ScoreKeySignature, ScorePart, assemble_score
from .spelling import PitchSpellingContext


@dataclass(frozen=True)
class PartTranscriptionRequest:
    part_id: str
    name: str
    instrument: str
    events: tuple[CommittedPerformanceEvent, ...]
    staffs: tuple[StaffProfile, ...]
    spelling_context: PitchSpellingContext = PitchSpellingContext()
    directive: InstrumentNotationDirective | None = None

    def validate(self) -> None:
        if not self.part_id or not self.name or not self.instrument:
            raise ValueError("part transcription identity is required")
        if not self.events:
            raise ValueError("part transcription requires events")
        if not self.staffs:
            raise ValueError("part transcription requires staff profiles")
        for event in self.events:
            event.validate()


@dataclass(frozen=True)
class PartTranscriptionResult:
    part: ScorePart
    projections: tuple[EventProjectionResult, ...]


@dataclass(frozen=True)
class TakeTranscriptionResult:
    score: ReadableScore
    parts: tuple[PartTranscriptionResult, ...]


def _event_sort_key(event: CommittedPerformanceEvent) -> tuple[float, float, str]:
    beat = event.time.transport_beat
    return (
        beat if beat is not None else float("inf"),
        event.time.onset_seconds,
        event.event_id,
    )


def transcribe_part(
    request: PartTranscriptionRequest,
    *,
    meter_numerator: int = 4,
    meter_denominator: int = 4,
) -> PartTranscriptionResult:
    """Project an ordered set of committed events into one readable score part."""

    request.validate()
    profile = resolve_instrument_profile(request.instrument)
    transposition = (
        profile.transposition if profile is not None else TranspositionSpec()
    )

    projections = tuple(
        project_pitched_event(
            event,
            part_id=request.part_id,
            staffs=request.staffs,
            spelling_context=request.spelling_context,
            directive=request.directive,
            transposition=transposition,
            meter_numerator=meter_numerator,
            meter_denominator=meter_denominator,
        )
        for event in sorted(request.events, key=_event_sort_key)
    )

    score_events = tuple(
        sorted(
            (
                score_event
                for projection in projections
                for score_event in projection.score_events
            ),
            key=lambda event: (
                event.span.onset,
                event.staff_id,
                event.voice_id,
                event.event_id,
            ),
        )
    )

    part = ScorePart(
        part_id=request.part_id,
        name=request.name,
        instrument=request.instrument,
        staff_ids=tuple(staff.staff_id for staff in request.staffs),
        events=score_events,
        profile_id=profile.profile_id if profile is not None else None,
    )
    part.validate()
    return PartTranscriptionResult(part=part, projections=projections)


def transcribe_take(
    requests: tuple[PartTranscriptionRequest, ...],
    *,
    score_id: str,
    title: str,
    meter_numerator: int = 4,
    meter_denominator: int = 4,
    key_signature: ScoreKeySignature = ScoreKeySignature(),
) -> TakeTranscriptionResult:
    """Produce a LogicalScore-ready take from one or more performance parts."""

    if not requests:
        raise ValueError("take transcription requires at least one part request")

    parts = tuple(
        transcribe_part(
            request,
            meter_numerator=meter_numerator,
            meter_denominator=meter_denominator,
        )
        for request in requests
    )
    score = assemble_score(
        score_id=score_id,
        title=title,
        parts=tuple(result.part for result in parts),
        meter_numerator=meter_numerator,
        meter_denominator=meter_denominator,
        key_signature=key_signature,
        provenance=("transcribe:batch-vertical-slice",),
    )
    return TakeTranscriptionResult(score=score, parts=parts)
