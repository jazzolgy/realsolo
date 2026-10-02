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
    rhythm_cell: str | None = None

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
            rhythm_cell=tag_value("rhythm_cell:"),
        )

    def similarity(self, other: "GestureSignature") -> float:
        pairs = (
            (self.role, other.role),
            (self.family, other.family),
            (self.rhythm, other.rhythm),
            (self.register, other.register),
            (self.dynamic, other.dynamic),
            (self.touch, other.touch),
            (self.rhythm_cell, other.rhythm_cell),
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
    pattern_consistency_strength: float = 0.0

    def validate(self) -> None:
        for name in (
            "variation_pressure",
            "groove_lock_strength",
            "motif_continuity_strength",
            "pattern_consistency_strength",
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
        lay_out_repeat = current.role == "lay_out" and current.family is None
        scale = 0.25 if lay_out_repeat else 1.0
        consistency_relief = 1.0 - 0.75 * context.pattern_consistency_strength
        penalty = -0.16 * context.variation_pressure * scale * consistency_relief
        add(
            "exact_repetition",
            penalty,
            "repeated lay-out is only lightly penalized because continued space can be intentional"
            if lay_out_repeat
            else "exact recent gesture repetition is mechanically redundant",
        )
    elif similarity >= 0.66:
        consistency_relief = 1.0 - 0.55 * context.pattern_consistency_strength
        penalty = -0.07 * context.variation_pressure * consistency_relief
        add("high_similarity", penalty, "highly similar recent gesture receives mild variation pressure")
    elif 0.25 <= similarity <= 0.65:
        add("balanced_variation", 0.04, "partial continuity with variation preserves identity without cloning")

    if (
        context.pattern_consistency_strength > 0
        and similarity >= 0.66
        and current.role != "lay_out"
    ):
        add(
            "pattern_consistency",
            0.06 * context.pattern_consistency_strength,
            "stable local comping pattern can support groove/form continuity",
        )

    # Groove continuity: allow same rhythmic placement if other dimensions move.
    if current.rhythm is not None and current.rhythm == last.rhythm:
        if similarity < 0.999 and context.groove_lock_strength > 0:
            add(
                "groove_continuity",
                0.06 * context.groove_lock_strength,
                "rhythmic continuity can preserve groove identity while other dimensions vary",
            )

    # Rhythmic repetition pressure is independent from voicing/family changes.
    # This prevents a mechanically repeated comping cell from hiding behind new
    # voicings. Stable vamp/groove evidence can explicitly relax the penalty.
    repetition_key = current.rhythm_cell or current.rhythm
    if repetition_key is not None:
        recent_rhythms = [
            (sig.rhythm_cell or sig.rhythm)
            for sig in recent[-4:]
            if (sig.rhythm_cell or sig.rhythm) is not None
        ]
        same_rhythm_count = sum(1 for rhythm in recent_rhythms if rhythm == repetition_key)
        consistency_relief = 1.0 - 0.85 * context.pattern_consistency_strength
        if same_rhythm_count >= 2:
            add(
                "rhythm_repetition_streak",
                -0.10 * context.variation_pressure * same_rhythm_count * consistency_relief,
                "repeated comping rhythm cell needs variation unless a real pattern is being preserved",
            )

        # Detect a short A-B-A-B loop. Real comping may repeat a motif, but absent
        # strong pattern evidence this loop should not become the default engine.
        if (
            len(recent_rhythms) >= 3
            and recent_rhythms[-2] == repetition_key
            and recent_rhythms[-3] == recent_rhythms[-1]
            and context.pattern_consistency_strength < 0.7
        ):
            add(
                "short_periodic_loop",
                -0.08 * context.variation_pressure,
                "short periodic comping loop is becoming mechanically predictable",
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
    if exact_count >= 2 and not (current.role == "lay_out" and current.family is None):
        add(
            "repetition_streak",
            -0.10 * context.variation_pressure * exact_count,
            "repetition streak increases pressure to change the current gesture",
        )

    return VariationScore(score, components, tuple(reasons))
