"""Variation and repetition intelligence for immediate piano comping.

The goal is not novelty for its own sake. Exact mechanical repetition is penalized,
while partial continuity can be rewarded when groove/motif identity should persist.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class GestureSignature:
    role: str
    family: str | None
    rhythm: str | None
    register: str | None
    dynamic: str | None
    touch: str | None

    @classmethod
    def from_candidate(cls, candidate: Any) -> "GestureSignature":
        role = candidate.role.value
        family = None
        if candidate.realization is not None:
            family = candidate.realization.event.source_family
        tags = set(candidate.tags)

        def tag_value(prefix: str) -> str | None:
            for tag in tags:
                if tag.startswith(prefix):
                    return tag.split(":", 1)[1]
            return None

        return cls(
            role=role,
            family=family,
            rhythm=tag_value("rhythm:"),
            register=tag_value("register:"),
            dynamic=tag_value("dynamic:"),
            touch=tag_value("touch:"),
        )

    def similarity(self, other: "GestureSignature") -> float:
        pairs = (
            (self.role, other.role),
            (self.family, other.family),
            (self.rhythm, other.rhythm),
            (self.register, other.register),
            (self.dynamic, other.dynamic),
            (self.touch, other.touch),
        )
        comparable = [(a, b) for a, b in pairs if a is not None and b is not None]
        if not comparable:
            return 0.0
        return sum(1 for a, b in comparable if a == b) / len(comparable)


@dataclass(frozen=True)
class VariationContext:
    variation_pressure: float = 0.5
    groove_lock_strength: float = 0.0
    motif_continuity_strength: float = 0.0

    def validate(self) -> None:
        for name in (
            "variation_pressure",
            "groove_lock_strength",
            "motif_continuity_strength",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


@dataclass(frozen=True)
class VariationScore:
    total: float
    components: Mapping[str, float]
    reasons: tuple[str, ...]


def evaluate_variation(
    candidate: Any,
    recent: Sequence[GestureSignature],
    context: VariationContext,
) -> VariationScore:
    context.validate()
    current = GestureSignature.from_candidate(candidate)
    score = 0.0
    components: dict[str, float] = {}
    reasons: list[str] = []

    def add(key: str, value: float, reason: str) -> None:
        nonlocal score
        score += value
        components[key] = components.get(key, 0.0) + value
        reasons.append(reason)

    if not recent:
        return VariationScore(0.0, {}, ())

    last = recent[-1]
    similarity = current.similarity(last)

    if similarity >= 0.999:
        penalty = -0.16 * context.variation_pressure
        add("exact_repetition", penalty, "exact recent gesture repetition is mechanically redundant")
    elif similarity >= 0.66:
        penalty = -0.07 * context.variation_pressure
        add("high_similarity", penalty, "highly similar recent gesture receives mild variation pressure")
    elif 0.25 <= similarity <= 0.65:
        add("balanced_variation", 0.04, "partial continuity with variation preserves identity without cloning")

    # Groove continuity: allow same rhythmic placement if other dimensions move.
    if current.rhythm is not None and current.rhythm == last.rhythm:
        if similarity < 0.999 and context.groove_lock_strength > 0:
            add(
                "groove_continuity",
                0.06 * context.groove_lock_strength,
                "rhythmic continuity can preserve groove identity while other dimensions vary",
            )

    # Motif continuity: allow same family/role when expression or timing changes.
    same_family_role = (
        current.family is not None
        and current.family == last.family
        and current.role == last.role
    )
    if same_family_role and similarity < 0.999 and context.motif_continuity_strength > 0:
        add(
            "motif_continuity",
            0.05 * context.motif_continuity_strength,
            "family/role continuity can support motif-like development when realization changes",
        )

    # Strong variation pressure after repeated same signatures in recent memory.
    exact_count = sum(1 for sig in recent[-3:] if current.similarity(sig) >= 0.999)
    if exact_count >= 2:
        add(
            "repetition_streak",
            -0.10 * context.variation_pressure * exact_count,
            "repetition streak increases pressure to change the current gesture",
        )

    return VariationScore(score, components, tuple(reasons))
