"""Readable dynamic-trajectory inference from committed performance evidence.

The goal is not to engrave raw amplitude.  It decides whether a sequence of
performed dynamic levels is best represented as no extra notation, a discrete
dynamic change, or a gradual crescendo/diminuendo hairpin.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .events import CommittedPerformanceEvent
from .score import ScoreEvent, ScoreSpanner, ScoreSpannerKind


class DynamicTrajectoryKind(str, Enum):
    NONE = "none"
    STEP_CHANGE = "step_change"
    CRESCENDO = "crescendo"
    DIMINUENDO = "diminuendo"


@dataclass(frozen=True)
class DynamicTrajectoryCandidate:
    kind: DynamicTrajectoryKind
    source_event_ids: tuple[str, ...]
    start_level: float
    end_level: float
    total_delta: float
    monotonic_ratio: float
    confidence: float
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.source_event_ids:
            raise ValueError("dynamic trajectory requires source events")
        for value in (self.start_level, self.end_level):
            if not 0.0 <= value <= 1.0:
                raise ValueError("dynamic levels must be within 0..1")
        if not 0.0 <= self.monotonic_ratio <= 1.0:
            raise ValueError("monotonic_ratio must be within 0..1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


def infer_dynamic_trajectory(
    events: tuple[CommittedPerformanceEvent, ...],
    *,
    minimum_hairpin_delta: float = .18,
    minimum_monotonic_ratio: float = .70,
    step_jump_threshold: float = .16,
) -> DynamicTrajectoryCandidate:
    """Infer the most readable dynamic notation for an ordered event sequence."""

    if len(events) < 2:
        raise ValueError("dynamic trajectory requires at least two events")

    ordered = tuple(sorted(events, key=lambda e: e.time.onset_seconds))
    for event in ordered:
        event.validate()
        if event.dynamic is None:
            raise ValueError("all trajectory events require dynamic evidence")

    levels = tuple(float(e.dynamic) for e in ordered)
    deltas = tuple(b - a for a, b in zip(levels, levels[1:]))
    total_delta = levels[-1] - levels[0]
    abs_total = abs(total_delta)
    direction = 1 if total_delta > 0 else -1 if total_delta < 0 else 0

    if direction == 0:
        return DynamicTrajectoryCandidate(
            DynamicTrajectoryKind.NONE,
            tuple(e.event_id for e in ordered),
            levels[0],
            levels[-1],
            total_delta,
            1.0,
            1.0,
            reasons=("no net dynamic direction",),
        )

    agreeing = sum(1 for d in deltas if d == 0 or (d > 0) == (direction > 0))
    monotonic_ratio = agreeing / len(deltas)
    largest_jump = max(abs(d) for d in deltas)

    # A short sudden level change is better shown as a new dynamic marking than
    # as a hairpin implying a gradual transition.
    if largest_jump >= step_jump_threshold and len(ordered) <= 3:
        confidence = min(1.0, .55 + largest_jump)
        return DynamicTrajectoryCandidate(
            DynamicTrajectoryKind.STEP_CHANGE,
            tuple(e.event_id for e in ordered),
            levels[0],
            levels[-1],
            total_delta,
            monotonic_ratio,
            confidence,
            reasons=("dominant sudden level change favors discrete dynamic",),
        )

    if (
        len(ordered) >= 3
        and abs_total >= minimum_hairpin_delta
        and monotonic_ratio >= minimum_monotonic_ratio
    ):
        kind = (
            DynamicTrajectoryKind.CRESCENDO
            if direction > 0
            else DynamicTrajectoryKind.DIMINUENDO
        )
        confidence = min(
            1.0,
            .45 + abs_total + .30 * monotonic_ratio,
        )
        return DynamicTrajectoryCandidate(
            kind,
            tuple(e.event_id for e in ordered),
            levels[0],
            levels[-1],
            total_delta,
            monotonic_ratio,
            confidence,
            reasons=(
                "sustained directional dynamic change",
                "small local deviations may be absorbed into a readable hairpin",
            ),
        )

    return DynamicTrajectoryCandidate(
        DynamicTrajectoryKind.NONE,
        tuple(e.event_id for e in ordered),
        levels[0],
        levels[-1],
        total_delta,
        monotonic_ratio,
        max(0.0, 1.0 - abs_total),
        reasons=("change is too small or inconsistent for extra notation",),
    )


def score_spanner_from_dynamic_trajectory(
    candidate: DynamicTrajectoryCandidate,
    *,
    part_id: str,
    score_events: tuple[ScoreEvent, ...],
    spanner_id: str | None = None,
) -> ScoreSpanner | None:
    """Map a gradual trajectory to score endpoints without redoing rhythm logic."""

    candidate.validate()
    if candidate.kind not in {
        DynamicTrajectoryKind.CRESCENDO,
        DynamicTrajectoryKind.DIMINUENDO,
    }:
        return None

    source_order = {sid: i for i, sid in enumerate(candidate.source_event_ids)}
    matched = [
        event
        for event in score_events
        if any(sid in source_order for sid in event.source_event_ids)
    ]
    if len(matched) < 2:
        raise ValueError("score events do not cover dynamic trajectory endpoints")

    def source_rank(event: ScoreEvent) -> int:
        ranks = [
            source_order[sid]
            for sid in event.source_event_ids
            if sid in source_order
        ]
        return min(ranks) if ranks else 10**9

    matched.sort(key=lambda event: (source_rank(event), event.span.onset, event.event_id))
    start = matched[0]
    end = matched[-1]
    if start.part_id != part_id or end.part_id != part_id:
        raise ValueError("dynamic trajectory score events must belong to part")

    kind = (
        ScoreSpannerKind.CRESCENDO
        if candidate.kind is DynamicTrajectoryKind.CRESCENDO
        else ScoreSpannerKind.DIMINUENDO
    )
    result = ScoreSpanner(
        spanner_id=spanner_id or (
            f"dynamic:{candidate.kind.value}:{candidate.source_event_ids[0]}:"
            f"{candidate.source_event_ids[-1]}"
        ),
        kind=kind,
        part_id=part_id,
        start_event_id=start.event_id,
        end_event_id=end.event_id,
        provenance=("transcribe:dynamic-trajectory-inference",),
    )
    result.validate()
    return result
