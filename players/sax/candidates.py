"""Legend-aware soft candidate material for Sax.

This module does not generate future note sequences. It only exposes immediate
candidate-source evidence that the Sax policy may use when forming the next
event.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.legends import LegendDomain, VocabularyUseType
from .legend_context import SaxLegendContext


@dataclass(frozen=True)
class SaxLegendCandidateContext:
    domain: LegendDomain
    harmony_context: str = ""
    harmonic_function: str = ""
    local_key: str = ""
    phrase_position: str = ""
    active_tags: tuple[str, ...] = ()
    allowed_uses: frozenset[VocabularyUseType] = frozenset(VocabularyUseType)
    vocabulary_limit: int = 8


@dataclass(frozen=True)
class SaxLegendCandidateMaterial:
    source_family: str
    domain: LegendDomain
    feature: str = ""
    vocabulary_id: str = ""
    use_type: VocabularyUseType | None = None
    score_bias: float = 0.0
    confidence: float = 1.0
    recent_usage_count: int = 0
    reasons: tuple[str, ...] = ()


def collect_legend_candidate_material(
    legend: SaxLegendContext,
    context: SaxLegendCandidateContext,
) -> tuple[SaxLegendCandidateMaterial, ...]:
    out: list[SaxLegendCandidateMaterial] = []

    for tendency in legend.tendencies(
        domain=context.domain,
        active_tags=context.active_tags,
    ):
        bias = legend.feature_bias(
            domain=context.domain,
            feature=tendency.feature,
            active_tags=context.active_tags,
        )
        out.append(SaxLegendCandidateMaterial(
            source_family="legend_prior",
            domain=context.domain,
            feature=tendency.feature,
            score_bias=bias,
            confidence=tendency.confidence,
            reasons=(tendency.tendency_id,),
        ))

    memories = legend.vocabulary(
        domain=context.domain,
        harmony_context=context.harmony_context,
        harmonic_function=context.harmonic_function,
        local_key=context.local_key,
        phrase_position=context.phrase_position,
        context_tags=frozenset(context.active_tags),
        allowed_uses=context.allowed_uses,
        limit=context.vocabulary_limit,
    )
    for item in memories:
        supported_uses = tuple(
            use for use in context.allowed_uses
            if use in item.candidate_uses
        )
        for use in supported_uses:
            repetition_pressure = min(.25, .04 * item.recent_usage_count)
            out.append(SaxLegendCandidateMaterial(
                source_family="legend_vocabulary",
                domain=context.domain,
                vocabulary_id=item.vocabulary_id,
                use_type=use,
                score_bias=item.confidence - repetition_pressure,
                confidence=item.confidence,
                recent_usage_count=item.recent_usage_count,
                reasons=(item.source_id, f"use:{use.value}"),
            ))

    return tuple(sorted(
        out,
        key=lambda x: (x.score_bias, x.confidence, x.vocabulary_id, x.feature),
        reverse=True,
    ))
