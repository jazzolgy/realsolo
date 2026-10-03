"""Batch transcription vertical slice from Performance Evidence to LogicalScore.

This module intentionally consumes only the transcription-side committed
performance contract.  It has no dependency on Audio Evidence Engine internals.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from fractions import Fraction

from .allocation import StaffProfile
from .dynamics import (
    DynamicTrajectoryCandidate,
    DynamicTrajectoryKind,
    infer_dynamic_trajectory,
    score_spanner_from_dynamic_trajectory,
)
from .events import CommittedPerformanceEvent
from .instrument_profiles import TranspositionSpec, resolve_instrument_profile
from .instrument_rules import InstrumentNotationDirective
from .notation import NotatedAtomKind, ScoreSpan
from .piano import (
    PianoGestureCandidate,
    apply_piano_gesture_candidate,
    piano_gesture_candidates,
)
from .projection import EventProjectionResult, project_pitched_event
from .score import (
    ReadableScore,
    ScoreEvent,
    ScoreKeySignature,
    ScorePart,
    ScoreSpanner,
    assemble_score,
)
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
    materialize_rests: bool = True
    infer_piano_gestures: bool = True
    infer_dynamic_hairpins: bool = True

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
    piano_gestures: tuple[PianoGestureCandidate, ...] = ()
    dynamic_trajectory: DynamicTrajectoryCandidate | None = None
    spanners: tuple[ScoreSpanner, ...] = ()


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



def _materialize_voice_rests(
    events: tuple[ScoreEvent, ...],
    *,
    start: Fraction = Fraction(0),
) -> tuple[ScoreEvent, ...]:
    """Insert readable rests in gaps without changing sounding-note evidence."""

    groups: dict[tuple[str, str, str], list[ScoreEvent]] = {}
    for event in events:
        groups.setdefault(
            (event.part_id, event.staff_id, event.voice_id),
            [],
        ).append(event)

    out: list[ScoreEvent] = []
    rest_counter = 0
    for (part_id, staff_id, voice_id), voice_events in groups.items():
        voice_events.sort(key=lambda event: (event.span.onset, event.event_id))
        cursor = start
        seen_groups: set[str] = set()
        for event in voice_events:
            chord_member = (
                event.simultaneity_group_id is not None
                and event.simultaneity_group_id in seen_groups
            )
            if not chord_member and event.span.onset > cursor:
                rest_counter += 1
                out.append(
                    ScoreEvent(
                        event_id=f"rest:{part_id}:{staff_id}:{voice_id}:{rest_counter}",
                        part_id=part_id,
                        staff_id=staff_id,
                        voice_id=voice_id,
                        kind=NotatedAtomKind.REST,
                        span=ScoreSpan(cursor, event.span.onset - cursor),
                        provenance=("transcribe:voice-gap-rest",),
                    )
                )
            out.append(event)
            if event.simultaneity_group_id is not None:
                seen_groups.add(event.simultaneity_group_id)
            if not chord_member:
                cursor = max(cursor, event.span.offset)

    return tuple(
        sorted(
            out,
            key=lambda event: (
                event.span.onset,
                event.staff_id,
                event.voice_id,
                0 if event.kind is NotatedAtomKind.REST else 1,
                event.event_id,
            ),
        )
    )


def _apply_piano_gestures(
    request: PartTranscriptionRequest,
    score_events: tuple[ScoreEvent, ...],
) -> tuple[tuple[ScoreEvent, ...], tuple[PianoGestureCandidate, ...]]:
    if not request.infer_piano_gestures or "piano" not in request.instrument.lower():
        return score_events, ()

    grouped: dict[str, list[CommittedPerformanceEvent]] = {}
    for event in request.events:
        if event.gesture_id is not None:
            grouped.setdefault(event.gesture_id, []).append(event)

    current = score_events
    selected: list[PianoGestureCandidate] = []
    for gesture_id, source_events in sorted(grouped.items()):
        if len(source_events) < 2:
            continue
        candidates = piano_gesture_candidates(tuple(source_events))
        for candidate in candidates:
            try:
                updated = apply_piano_gesture_candidate(
                    candidate,
                    current,
                    simultaneity_group_id=f"piano:{request.part_id}:{gesture_id}",
                )
            except ValueError:
                continue
            current = updated
            selected.append(candidate)
            break

    return current, tuple(selected)


def _infer_part_dynamic(
    request: PartTranscriptionRequest,
    score_events: tuple[ScoreEvent, ...],
) -> tuple[DynamicTrajectoryCandidate | None, tuple[ScoreSpanner, ...]]:
    if not request.infer_dynamic_hairpins:
        return None, ()
    dynamic_events = tuple(
        event for event in sorted(request.events, key=_event_sort_key)
        if event.dynamic is not None
    )
    if len(dynamic_events) < 3:
        return None, ()

    candidate = infer_dynamic_trajectory(dynamic_events)
    if candidate.kind not in {
        DynamicTrajectoryKind.CRESCENDO,
        DynamicTrajectoryKind.DIMINUENDO,
    }:
        return candidate, ()

    spanner = score_spanner_from_dynamic_trajectory(
        candidate,
        part_id=request.part_id,
        score_events=score_events,
    )
    return candidate, (spanner,) if spanner is not None else ()


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

    score_events, selected_piano_gestures = _apply_piano_gestures(
        request,
        score_events,
    )
    dynamic_trajectory, spanners = _infer_part_dynamic(
        request,
        score_events,
    )
    if request.materialize_rests:
        score_events = _materialize_voice_rests(score_events)

    part = ScorePart(
        part_id=request.part_id,
        name=request.name,
        instrument=request.instrument,
        staff_ids=tuple(staff.staff_id for staff in request.staffs),
        events=score_events,
        profile_id=profile.profile_id if profile is not None else None,
    )
    part.validate()
    return PartTranscriptionResult(
        part=part,
        projections=projections,
        piano_gestures=selected_piano_gestures,
        dynamic_trajectory=dynamic_trajectory,
        spanners=spanners,
    )


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
        spanners=tuple(
            spanner
            for result in parts
            for spanner in result.spanners
        ),
        meter_numerator=meter_numerator,
        meter_denominator=meter_denominator,
        key_signature=key_signature,
        provenance=("transcribe:batch-vertical-slice",),
    )
    return TakeTranscriptionResult(score=score, parts=parts)
