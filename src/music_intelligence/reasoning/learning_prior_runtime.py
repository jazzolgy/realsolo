"""Runtime adapters for learned priors.

Runtime reasoning consumes only LearningPriorView, never learner/store internals.
Learned priors are soft biases: they may nudge candidate scores or confidence,
but they never force an event, phrase, interaction, or groove.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import fmod

from music_intelligence.learning.engine import LearningPriorView


@dataclass(frozen=True)
class PriorBias:
    score_delta: float = 0.0
    confidence_delta: float = 0.0
    reason: str = ""

    @property
    def active(self) -> bool:
        return bool(self.score_delta or self.confidence_delta)


def numeric_target_bias(
    prior: LearningPriorView | None,
    feature: str,
    observed: float,
    *,
    tolerance: float,
    max_bonus: float = 0.08,
    max_penalty: float = 0.04,
    minimum_weight: float = 0.25,
) -> PriorBias:
    """Softly reward proximity to a learned numeric tendency.

    The prior's accumulated effective weight controls trust. With little
    evidence, the bias fades toward zero.
    """

    if prior is None or tolerance <= 0:
        return PriorBias()
    learned = prior.numeric_features.get(feature)
    if learned is None:
        return PriorBias()

    feature_weight = prior.numeric_weights.get(feature, prior.weighted_observations)
    trust = max(0.0, min(1.0, feature_weight / max(minimum_weight, 1.0)))
    if trust <= 0:
        return PriorBias()

    distance = abs(float(observed) - float(learned))
    closeness = max(0.0, 1.0 - distance / tolerance)
    delta = trust * (closeness * max_bonus - (1.0 - closeness) * max_penalty)
    return PriorBias(
        score_delta=delta,
        reason=f"learned prior {feature} target={learned:.3f}, observed={observed:.3f}",
    )


def circular_phase_bias(
    prior: LearningPriorView | None,
    feature: str,
    observed_phase: float,
    *,
    cycle: float,
    tolerance: float,
    max_bonus: float = 0.07,
    max_penalty: float = 0.03,
) -> PriorBias:
    """Numeric prior bias for cyclic metric positions."""

    if prior is None or cycle <= 0:
        return PriorBias()
    learned = prior.numeric_features.get(feature)
    if learned is None:
        return PriorBias()
    a = fmod(float(observed_phase), cycle)
    b = fmod(float(learned), cycle)
    if a < 0:
        a += cycle
    if b < 0:
        b += cycle
    direct = abs(a - b)
    distance = min(direct, cycle - direct)

    feature_weight = prior.numeric_weights.get(feature, prior.weighted_observations)
    trust = max(0.0, min(1.0, feature_weight))
    closeness = max(0.0, 1.0 - distance / tolerance) if tolerance > 0 else 0.0
    delta = trust * (closeness * max_bonus - (1.0 - closeness) * max_penalty)
    return PriorBias(
        score_delta=delta,
        reason=f"learned cyclic prior {feature} target={b:.3f}, observed={a:.3f}",
    )


def categorical_prior_bias(
    prior: LearningPriorView | None,
    feature: str,
    value: str,
    *,
    max_bonus: float = 0.08,
) -> PriorBias:
    """Return a bounded soft bias from a weighted categorical prior."""

    if prior is None or not value:
        return PriorBias()
    weight = prior.category_weight(feature, value)
    if weight <= 0:
        return PriorBias()
    # Positive-only by default: absence from the learned corpus is not evidence
    # that a valid musical option is wrong.
    delta = max_bonus * max(0.0, min(1.0, weight))
    return PriorBias(
        score_delta=delta,
        confidence_delta=delta * 0.5,
        reason=f"learned categorical prior {feature}={value} weight={weight:.3f}",
    )


def strongest_category(
    prior: LearningPriorView | None,
    feature: str,
) -> tuple[str, float] | None:
    """Return the strongest weighted category without reaching into learner state."""

    if prior is None:
        return None
    weighted = prior.categorical_weights.get(feature, {})
    if weighted:
        total = sum(weighted.values())
        if total <= 0:
            return None
        label, value = max(weighted.items(), key=lambda kv: (kv[1], kv[0]))
        return label, value / total

    counts = prior.categorical_counts.get(feature, {})
    if not counts:
        return None
    total = sum(counts.values())
    label, value = max(counts.items(), key=lambda kv: (kv[1], kv[0]))
    return label, value / total if total else 0.0
