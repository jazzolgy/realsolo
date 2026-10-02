"""Contextual mixture helpers for multiple LegendProfileView objects."""
from __future__ import annotations

from dataclasses import dataclass

from .interfaces import LegendDomain, LegendProfileView, LegendQueryContext, LegendTendencyMatch


@dataclass(frozen=True)
class LegendViewWeight:
    view: LegendProfileView
    weight: float = 1.0


def query_mixture(
    views: tuple[LegendViewWeight, ...],
    domain: LegendDomain,
    context: LegendQueryContext = LegendQueryContext(),
) -> tuple[LegendTendencyMatch, ...]:
    """Mix evidence per domain/context, never by splicing stored future phrases."""
    out: list[LegendTendencyMatch] = []
    for weighted in views:
        if weighted.weight < 0:
            raise ValueError("legend mixture weights cannot be negative")
        for m in weighted.view.query(domain, context):
            out.append(LegendTendencyMatch(
                profile_id=m.profile_id,
                tendency_id=m.tendency_id,
                feature=m.feature,
                weighted_bias=m.weighted_bias * weighted.weight,
                confidence=m.confidence,
                provenance=m.provenance,
                note=m.note,
            ))
    return tuple(sorted(out, key=lambda x: abs(x.weighted_bias), reverse=True))
