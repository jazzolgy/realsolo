"""Dimension-specific continuity and coherence-preserving creativity.

Creativity here is not random novelty. The pianist can preserve selected musical
anchors while changing other realization dimensions. This makes creative response
possible in every context, including highly stable vamps and highly constrained
support situations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .harmonic_continuity import HarmonicContinuityFeatures
from .variation import GestureSignature


@dataclass(frozen=True)
class DimensionContinuityProfile:
    role: float = 0.5
    family: float = 0.5
    rhythm: float = 0.5
    register: float = 0.3
    dynamic: float = 0.25
    touch: float = 0.25

    def validate(self) -> None:
        for name in ("role", "family", "rhythm", "register", "dynamic", "touch"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")

    def as_mapping(self) -> Mapping[str, float]:
        self.validate()
        return {
            "role": self.role,
            "family": self.family,
            "rhythm": self.rhythm,
            "register": self.register,
            "dynamic": self.dynamic,
            "touch": self.touch,
        }


@dataclass(frozen=True)
class CreativityContext:
    creativity_strength: float = 0.55
    coherence_floor: float = 0.30

    def validate(self) -> None:
        if not 0.0 <= self.creativity_strength <= 1.0:
            raise ValueError("creativity_strength must be within 0..1")
        if not 0.0 <= self.coherence_floor <= 1.0:
            raise ValueError("coherence_floor must be within 0..1")


@dataclass(frozen=True)
class CreativeContinuityScore:
    total: float
    components: Mapping[str, float]
    reasons: tuple[str, ...]


def profile_from_harmonic_context(
    features: HarmonicContinuityFeatures | None,
) -> DimensionContinuityProfile:
    """Derive which dimensions should remain stable from current harmony/form.

    A stable/repeating harmonic context raises rhythmic and role continuity more than
    expressive continuity. Near boundaries, all structural anchors loosen so a new
    texture can emerge.
    """
    if features is None:
        return DimensionContinuityProfile()

    features.validate()
    pattern = features.pattern_consistency_strength
    recurrence = features.recurrence_strength
    hold = features.hold_stability
    boundary = features.boundary_pressure

    loosen = 1.0 - 0.65 * boundary

    profile = DimensionContinuityProfile(
        role=max(0.15, min(1.0, (0.34 + 0.34 * pattern + 0.12 * hold) * loosen)),
        family=max(0.10, min(1.0, (0.28 + 0.28 * pattern + 0.18 * hold) * loosen)),
        rhythm=max(0.12, min(1.0, (0.30 + 0.42 * recurrence + 0.22 * pattern) * loosen)),
        register=max(0.08, min(1.0, (0.16 + 0.16 * hold) * loosen)),
        dynamic=max(0.05, min(1.0, (0.12 + 0.10 * pattern) * loosen)),
        touch=max(0.05, min(1.0, (0.12 + 0.10 * recurrence) * loosen)),
    )
    profile.validate()
    return profile


def _dimension_values(signature: GestureSignature) -> Mapping[str, str | None]:
    return {
        "role": signature.role,
        "family": signature.family,
        "rhythm": signature.rhythm,
        "register": signature.register,
        "dynamic": signature.dynamic,
        "touch": signature.touch,
    }


def evaluate_creative_continuity(
    candidate: Any,
    previous: GestureSignature | None,
    profile: DimensionContinuityProfile,
    context: CreativityContext,
) -> CreativeContinuityScore:
    """Reward novelty on freer dimensions while retaining enough musical coherence."""
    profile.validate()
    context.validate()
    if previous is None:
        return CreativeContinuityScore(0.0, {}, ())

    current = GestureSignature.from_candidate(candidate)
    if current.role == "lay_out" and current.family is None:
        # Silence can itself be a creative decision; do not force decorative change.
        return CreativeContinuityScore(0.0, {}, ())

    now = _dimension_values(current)
    before = _dimension_values(previous)
    weights = profile.as_mapping()

    score = 0.0
    components: dict[str, float] = {}
    reasons: list[str] = []

    preserved_weight = 0.0
    changed_freedom = 0.0
    comparable_weight = 0.0
    changed_axes = 0

    for axis, weight in weights.items():
        a = now[axis]
        b = before[axis]
        if a is None or b is None:
            continue
        comparable_weight += weight
        if a == b:
            preserved_weight += weight
        else:
            changed_axes += 1
            # The lower the continuity requirement, the more useful a change can be.
            freedom = 1.0 - weight
            changed_freedom += freedom
            delta = 0.035 * context.creativity_strength * freedom
            if delta:
                components[f"creative_change:{axis}"] = delta
                score += delta
                reasons.append(f"creative change in relatively free {axis} dimension")

    if comparable_weight > 0:
        coherence = preserved_weight / comparable_weight
    else:
        coherence = 0.0

    if changed_axes == 0:
        penalty = -0.08 * context.creativity_strength
        score += penalty
        components["creative_stagnation"] = penalty
        reasons.append("all comparable dimensions repeat with no creative development")
    elif coherence >= context.coherence_floor:
        bonus = min(0.08, 0.018 * changed_axes + 0.015 * changed_freedom)
        bonus *= context.creativity_strength
        score += bonus
        components["coherent_novelty"] = bonus
        reasons.append("candidate changes free dimensions while preserving enough continuity")
    else:
        penalty = -0.06 * (context.coherence_floor - coherence)
        score += penalty
        components["coherence_loss"] = penalty
        reasons.append("too many high-continuity anchors change simultaneously")

    return CreativeContinuityScore(score, components, tuple(reasons))
