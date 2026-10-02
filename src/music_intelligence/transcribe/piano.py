"""Piano-specific *notation* interpretation of polyphonic gestures.

This module does not generate piano music.  It decides how already-performed
piano events may be represented readably: simultaneous chord, arpeggiated
gesture, or separated onset notation.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .events import CommittedPerformanceEvent
from .score import ScoreEvent


@dataclass(frozen=True)
class PianoGestureCandidate:
    kind: str
    source_event_ids: tuple[str, ...]
    onset_spread_seconds: float
    cost: float
    confidence: float
    markings: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.kind not in {"simultaneous_chord", "arpeggiated_chord", "separate_onsets"}:
            raise ValueError("unknown piano gesture notation kind")
        if not self.source_event_ids:
            raise ValueError("piano gesture candidate requires source events")
        if self.onset_spread_seconds < 0 or self.cost < 0:
            raise ValueError("spread/cost may not be negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


def piano_gesture_candidates(
    events: tuple[CommittedPerformanceEvent, ...],
    *,
    chord_tolerance_seconds: float = .035,
    spread_tolerance_seconds: float = .120,
) -> tuple[PianoGestureCandidate, ...]:
    if not events:
        raise ValueError("piano gesture requires events")
    for event in events:
        event.validate()
        if "piano" not in event.instrument.lower():
            raise ValueError("piano gesture received non-piano event")

    gesture_ids = {event.gesture_id for event in events}
    if len(gesture_ids) != 1 or None in gesture_ids:
        raise ValueError("events must share one explicit gesture_id")

    onsets = [e.time.onset_seconds for e in events]
    spread = max(onsets) - min(onsets)
    source_ids = tuple(e.event_id for e in events)
    techniques = {t for e in events for t in e.technique}
    explicit_roll = bool(techniques & {"roll", "rolled", "arpeggio", "arpeggiated"})

    simultaneous_cost = max(0.0, spread - chord_tolerance_seconds) * 8.0
    if explicit_roll:
        simultaneous_cost += .45

    arpeggio_cost = abs(spread - .055) * 2.5
    if explicit_roll:
        arpeggio_cost = max(0.0, arpeggio_cost - .35)
    if spread > spread_tolerance_seconds:
        arpeggio_cost += .18

    separate_cost = .14 if spread > spread_tolerance_seconds else .38
    if explicit_roll:
        separate_cost += .12

    candidates = (
        PianoGestureCandidate(
            "simultaneous_chord",
            source_ids,
            spread,
            simultaneous_cost,
            max(0.0, min(1.0, 1.0 - simultaneous_cost)),
            reasons=("shared gesture may collapse micro-stagger into one sonority",),
        ),
        PianoGestureCandidate(
            "arpeggiated_chord",
            source_ids,
            spread,
            max(0.0, arpeggio_cost),
            max(0.0, min(1.0, 1.0 - max(0.0, arpeggio_cost))),
            markings=("arpeggiate",),
            reasons=("preserves spread as gesture rather than literal microtiming",),
        ),
        PianoGestureCandidate(
            "separate_onsets",
            source_ids,
            spread,
            separate_cost,
            max(0.0, min(1.0, 1.0 - separate_cost)),
            reasons=("retains onset distinction when musically structural",),
        ),
    )
    for candidate in candidates:
        candidate.validate()
    return tuple(sorted(candidates, key=lambda c: (c.cost, -c.confidence, c.kind)))



def apply_piano_gesture_candidate(
    candidate: PianoGestureCandidate,
    score_events: tuple[ScoreEvent, ...],
    *,
    simultaneity_group_id: str | None = None,
) -> tuple[ScoreEvent, ...]:
    """Apply a chosen piano notation gesture to already-projected score events.

    The gesture decision never re-quantizes or re-voices notes.  A simultaneous
    chord may be grouped only when the target score events already share the
    same staff, voice, onset and duration after notation projection.
    """

    candidate.validate()
    if not score_events:
        raise ValueError("score_events are required")

    source_ids = set(candidate.source_event_ids)
    matched = tuple(
        event
        for event in score_events
        if source_ids.intersection(event.source_event_ids)
    )
    if len(matched) != len(candidate.source_event_ids):
        raise ValueError("score events do not cover the piano gesture sources")

    if candidate.kind == "simultaneous_chord":
        if len(matched) < 2:
            raise ValueError("simultaneous chord requires at least two score notes")
        first = matched[0]
        expected = (
            first.part_id,
            first.staff_id,
            first.voice_id,
            first.span.onset,
            first.span.duration,
        )
        for event in matched[1:]:
            actual = (
                event.part_id,
                event.staff_id,
                event.voice_id,
                event.span.onset,
                event.span.duration,
            )
            if actual != expected:
                raise ValueError(
                    "simultaneous piano gesture requires a common "
                    "part/staff/voice/onset/duration after projection"
                )
        group_id = simultaneity_group_id or (
            "piano:simultaneity:" + ":".join(candidate.source_event_ids)
        )
        return tuple(
            replace(event, simultaneity_group_id=group_id)
            if event in matched
            else event
            for event in score_events
        )

    if candidate.kind == "arpeggiated_chord":
        first_id = matched[0].event_id
        return tuple(
            replace(
                event,
                markings=tuple(dict.fromkeys(event.markings + candidate.markings)),
            )
            if event.event_id == first_id
            else event
            for event in score_events
        )

    return score_events
