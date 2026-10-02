"""Sax musical-policy owner for legend, score, and interaction context.

This layer chooses soft intention and permission. Pitch/rhythm realization
remains an immediate-event decision in candidates.py.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.corpus import ScoreContextSnapshot
from music_intelligence.legends import VocabularyUseType
from music_intelligence.reasoning.interaction_scheduler import InteractionDirective

from .candidates import (
    SaxLegendCandidateContext,
    SaxLegendCandidateMaterial,
    collect_legend_candidate_material,
)
from .interaction import SaxInteractionDecision, interpret_sax_interaction
from .legend_context import SaxLegendContext, SaxMemoryIntention
from .score_context import (
    SaxScoreActivity,
    SaxScorePolicyContext,
    interpret_score_context,
)


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


@dataclass(frozen=True)
class SaxRuntimePolicyDecision:
    score: SaxScorePolicyContext
    interaction: SaxInteractionDecision
    legend: SaxLegendPolicyDecision | None
    allow_improvisation: bool
    reasons: tuple[str, ...] = ()


def choose_sax_runtime_policy(
    score_snapshot: ScoreContextSnapshot,
    *,
    previous_score_snapshot: ScoreContextSnapshot | None = None,
    legend: SaxLegendContext | None = None,
    legend_candidate_context: SaxLegendCandidateContext | None = None,
    interaction_directive: InteractionDirective | None = None,
    external_allow_improvisation: bool = False,
) -> SaxRuntimePolicyDecision:
    score = interpret_score_context(
        score_snapshot,
        previous=previous_score_snapshot,
    )
    interaction = interpret_sax_interaction(interaction_directive, score)

    legend_decision = None
    if legend is not None and legend_candidate_context is not None:
        legend_decision = choose_legend_memory_intention(
            legend,
            legend_candidate_context,
        )

    if interaction.suppress_free_improvisation:
        allow = False
    elif score.activity is SaxScoreActivity.OPEN_SOLO:
        allow = True
    elif score.activity is SaxScoreActivity.UNSPECIFIED:
        allow = external_allow_improvisation
    else:
        allow = False

    reasons = list(score.reasons)
    reasons.extend(interaction.reasons)
    if legend_decision is not None:
        reasons.extend(legend_decision.reason)

    return SaxRuntimePolicyDecision(
        score=score,
        interaction=interaction,
        legend=legend_decision,
        allow_improvisation=allow,
        reasons=tuple(reasons),
    )
