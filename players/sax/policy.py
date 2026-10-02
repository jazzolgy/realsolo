"""Legend-aware Sax policy bridge.

This layer chooses a soft memory/prior intention. Pitch/rhythm realization is
still deferred to the immediate event generator and physical feasibility layer.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.legends import VocabularyUseType
from .candidates import (
    SaxLegendCandidateContext,
    SaxLegendCandidateMaterial,
    collect_legend_candidate_material,
)
from .legend_context import SaxLegendContext, SaxMemoryIntention


@dataclass(frozen=True)
class SaxLegendPolicyDecision:
    intention: SaxMemoryIntention | None
    materials: tuple[SaxLegendCandidateMaterial, ...]
    selected_feature: str = ""
    reason: tuple[str, ...] = ()


def choose_legend_memory_intention(
    legend: SaxLegendContext,
    context: SaxLegendCandidateContext,
) -> SaxLegendPolicyDecision:
    materials = collect_legend_candidate_material(legend, context)
    if not materials:
        return SaxLegendPolicyDecision(None, (), reason=("no legend material",))

    chosen = materials[0]
    if chosen.source_family == "legend_vocabulary" and chosen.use_type is not None:
        intention = SaxMemoryIntention(
            use_type=chosen.use_type,
            active_vocabulary_ids=(chosen.vocabulary_id,),
        )
        intention.validate()
        return SaxLegendPolicyDecision(
            intention,
            materials,
            reason=("selected contextual vocabulary memory",),
        )

    return SaxLegendPolicyDecision(
        None,
        materials,
        selected_feature=chosen.feature,
        reason=("selected contextual legend prior",),
    )
