"""Hierarchical runtime prior composition.

The hierarchy separates broad musical priors from narrower learned/style/legend
priors. Each layer contributes a bounded soft bias. No layer can force a
candidate or override current musical context by itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from music_intelligence.learning.engine import LearningPriorView
from music_intelligence.legends.interfaces import LegendDomain
from .legend_style_core import LegendBlend
from .learning_prior_runtime import PriorBias, numeric_target_bias


@dataclass(frozen=True)
class PriorLayerWeights:
    domain: float = 1.0
    genre: float = 0.45
    style: float = 0.60
    legend: float = 1.0

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if value < 0:
                raise ValueError(f"{name} prior weight cannot be negative")


@dataclass(frozen=True)
class HierarchicalPriorSet:
    """Stable runtime view across learned and evidence-informed prior layers."""

    domain_prior: LearningPriorView | None = None
    genre_prior: LearningPriorView | None = None
    style_prior: LearningPriorView | None = None
    legend_blend: LegendBlend | None = None
    weights: PriorLayerWeights = field(default_factory=PriorLayerWeights)

    def validate(self) -> None:
        self.weights.validate()
        if self.legend_blend is not None:
            self.legend_blend.validate()


@dataclass(frozen=True)
class HierarchicalBias:
    total: float
    components: Mapping[str, float] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()


def numeric_hierarchy_bias(
    priors: HierarchicalPriorSet | None,
    *,
    observed: float,
    domain_feature: str | None = None,
    genre_feature: str | None = None,
    style_feature: str | None = None,
    tolerance: float,
    max_bonus: float = 0.08,
    max_penalty: float = 0.04,
) -> HierarchicalBias:
    """Compose semantically equivalent numeric tendencies across layers."""

    if priors is None:
        return HierarchicalBias(0.0)
    priors.validate()

    total = 0.0
    components: dict[str, float] = {}
    reasons: list[str] = []

    for layer, prior, feature, weight in (
        ("domain", priors.domain_prior, domain_feature, priors.weights.domain),
        ("genre", priors.genre_prior, genre_feature, priors.weights.genre),
        ("style", priors.style_prior, style_feature, priors.weights.style),
    ):
        if prior is None or feature is None or weight <= 0:
            continue
        bias = numeric_target_bias(
            prior,
            feature,
            observed,
            tolerance=tolerance,
            max_bonus=max_bonus,
            max_penalty=max_penalty,
        )
        if not bias.active:
            continue
        contribution = bias.score_delta * weight
        total += contribution
        components[f"{layer}:{feature}"] = contribution
        reasons.append(f"{layer} prior: {bias.reason}")

    return HierarchicalBias(total, components, tuple(reasons))


def legend_feature_bias(
    priors: HierarchicalPriorSet | None,
    *,
    feature: str,
    active_tags: tuple[str, ...] = (),
) -> PriorBias:
    """Expose legend bias as one hierarchy layer without duplicating legend logic."""

    if priors is None or priors.legend_blend is None or priors.weights.legend <= 0:
        return PriorBias()
    priors.validate()
    value = priors.legend_blend.feature_bias(feature, active_tags) * priors.weights.legend
    if not value:
        return PriorBias()
    return PriorBias(
        score_delta=value,
        reason=f"legend prior {feature} bias={value:.3f}",
    )
