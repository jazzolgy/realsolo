"""Gap-driven research priority with explicit user override.

This module chooses *what to study next*, not how to interpret music. It never
downloads media or turns provider metadata into musical conclusions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class ResearchGap:
    dimension: str
    target: str
    gap: float
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.dimension.strip() or not self.target.strip():
            raise ValueError("dimension and target are required")
        if not 0.0 <= self.gap <= 1.0:
            raise ValueError("gap must be within 0..1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class ResearchPriorityOverride:
    """Temporary human steering, not a replacement fixed curriculum."""

    musician_weights: Mapping[str, float] = field(default_factory=dict)
    instrument_weights: Mapping[str, float] = field(default_factory=dict)
    dimension_weights: Mapping[str, float] = field(default_factory=dict)
    style_weights: Mapping[str, float] = field(default_factory=dict)
    note: str = ""

    def weight_for(self, dimension: str, target: str) -> float:
        table={
            "musician":self.musician_weights,
            "instrument":self.instrument_weights,
            "dimension":self.dimension_weights,
            "style":self.style_weights,
        }.get(dimension,{})
        return float(table.get(target,1.0))


def prioritize_research_gaps(
    gaps: tuple[ResearchGap,...],
    *,
    override: ResearchPriorityOverride | None = None,
) -> tuple[ResearchGap,...]:
    for gap in gaps:
        gap.validate()

    def score(gap: ResearchGap) -> float:
        boost=override.weight_for(gap.dimension,gap.target) if override else 1.0
        return gap.gap*gap.confidence*max(0.0,boost)

    return tuple(sorted(gaps,key=lambda x:(-score(x),x.dimension,x.target)))
