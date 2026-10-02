"""Abstract scorebook linear-practice comparator for Piano research.

This is an evaluation harness, not a new harmony/scale engine. It compares abstract
written-line observations against Shared Linear route families without storing a
copyrighted melody or exact phrase.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.harmony.scale_linear_core import LinearRouteKind


class IntervalMotionClass(str, Enum):
    STEPWISE = "stepwise"
    SMALL_MIXED = "small_mixed"
    LEAP_MIXED = "leap_mixed"
    REPETITIVE_CELL = "repetitive_cell"
    SUSTAINED = "sustained"
    MIXED = "mixed"


class MotionSourceClass(str, Enum):
    FIELD = "field"
    CHROMATIC = "chromatic"
    MIXED = "mixed"
    HARMONIC = "harmonic"
    OPEN = "open"


class ContourClass(str, Enum):
    RISING = "rising"
    FALLING = "falling"
    ARCH = "arch"
    VALLEY = "valley"
    OSCILLATING = "oscillating"
    STATIC = "static"
    MIXED = "mixed"


class TargetHorizonClass(str, Enum):
    IMMEDIATE = "immediate"
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AbstractWrittenLineObservation:
    observation_id: str
    song_id: str
    source_locator: str
    likely_routes: tuple[LinearRouteKind, ...]
    structural_targets: tuple[str, ...]
    interval_motion: IntervalMotionClass
    motion_source: MotionSourceClass
    contour: ContourClass
    target_horizon: TargetHorizonClass
    section_role: str
    rhythmic_density: str
    confidence: float
    provenance: tuple[str, ...]

    def validate(self) -> None:
        if not self.observation_id or not self.song_id or not self.source_locator:
            raise ValueError("observation identity and source locator are required")
        if not self.likely_routes:
            raise ValueError("at least one abstract route is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        if not self.provenance:
            raise ValueError("provenance is required")


@dataclass(frozen=True)
class LinearPracticeComparison:
    observed_routes: tuple[LinearRouteKind, ...]
    candidate_routes: tuple[LinearRouteKind, ...]
    route_recall: float
    extra_route_ratio: float
    target_alignment: float
    notes: tuple[str, ...]

    def validate(self) -> None:
        for value in (self.route_recall, self.extra_route_ratio, self.target_alignment):
            if not 0.0 <= value <= 1.0:
                raise ValueError("comparison metrics must be within 0..1")


def compare_abstract_routes(
    observation: AbstractWrittenLineObservation,
    candidate_routes: tuple[LinearRouteKind, ...],
    *,
    target_alignment: float = 1.0,
) -> LinearPracticeComparison:
    """Compare route-family coverage only; never compare literal note strings."""
    observation.validate()
    if not 0.0 <= target_alignment <= 1.0:
        raise ValueError("target_alignment must be within 0..1")

    observed=set(observation.likely_routes)
    candidates=set(candidate_routes)
    matched=observed & candidates
    route_recall=len(matched)/len(observed)

    extras=candidates-observed
    extra_route_ratio=(len(extras)/len(candidates)) if candidates else 0.0

    notes=[]
    if route_recall < 1.0:
        missing=sorted(x.value for x in observed-candidates)
        notes.append("missing observed route families: "+", ".join(missing))
    if extras:
        notes.append(
            "candidate-only route families: "
            + ", ".join(sorted(x.value for x in extras))
        )

    result=LinearPracticeComparison(
        observed_routes=observation.likely_routes,
        candidate_routes=tuple(candidate_routes),
        route_recall=route_recall,
        extra_route_ratio=extra_route_ratio,
        target_alignment=target_alignment,
        notes=tuple(notes),
    )
    result.validate()
    return result
