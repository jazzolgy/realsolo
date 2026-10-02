"""Bebop ensemble-breath bias for piano comping.

The evidence is ensemble-level and does not identify which player caused the breath.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .bebop_complementarity import (
    EnsembleBreathType,
    EnsembleComplementarityEvidence,
    SupportCarryMode,
    support_carry_mode,
)


@dataclass(frozen=True)
class BebopBreathCompingBias:
    total: float
    components: Mapping[str, float]
    reasons: tuple[str, ...]


def evaluate_bebop_breath_comping_bias(
    candidate,
    evidence: EnsembleComplementarityEvidence,
) -> BebopBreathCompingBias:
    evidence.validate()
    score = 0.0
    components: dict[str, float] = {}
    reasons: list[str] = []

    role = getattr(getattr(candidate, "role", None), "value", "")
    action = getattr(getattr(candidate, "action_type", None), "value", "")
    support = max(
        evidence.low_harmonic_support,
        evidence.percussive_support,
    )
    weight = evidence.confidence * max(evidence.foreground_drop, 0.25)

    def add(key: str, value: float, reason: str) -> None:
        nonlocal score
        score += value
        components[key] = components.get(key, 0.0) + value
        reasons.append(reason)

    if evidence.breath_type is EnsembleBreathType.FOREGROUND_HANDOFF:
        carry_mode = support_carry_mode(evidence)
        if role == "lay_out":
            add(
                "handoff_space",
                0.10 * weight * support,
                "active accompaniment support can carry the foreground handoff",
            )
        if action == "punctuation":
            add(
                "handoff_punctuation",
                0.06 * weight * support,
                "brief punctuation can answer without occupying the whole handoff",
            )
        if action == "sustained_support" and support >= 0.7:
            add(
                "handoff_overfill",
                -0.10 * weight * support,
                "sustained comping may overfill an already-supported handoff",
            )
        if role == "build" and support >= 0.75:
            add(
                "handoff_overbuild",
                -0.08 * weight * support,
                "build pressure conflicts with an already-carried handoff",
            )
        tags=set(getattr(candidate,"tags",()))
        realization=getattr(candidate,"realization",None)
        if realization is not None:
            tags |= set(realization.event.tags)

        if carry_mode is SupportCarryMode.HARMONIC_CARRIED:
            if action == "sustained_support":
                add(
                    "handoff_harmonic_duplicate",
                    -0.05 * weight,
                    "harmonic support already carries the handoff",
                )
            if action == "punctuation":
                add(
                    "handoff_harmonic_carried_punctuation",
                    0.04 * weight,
                    "brief punctuation can complement existing harmonic support",
                )

        elif carry_mode is SupportCarryMode.PERCUSSIVE_CARRIED:
            if action == "sparse_support" and (
                "guide_tone" in tags or "harmonic_identity" in tags
            ):
                add(
                    "handoff_percussive_carried_harmony",
                    0.05 * weight,
                    "percussive-carried handoff can admit thin harmonic identity",
                )

        elif carry_mode is SupportCarryMode.MIXED_SUPPORT:
            if role == "lay_out":
                add(
                    "handoff_mixed_support_space",
                    0.05 * weight,
                    "harmonic and percussive layers already carry the handoff",
                )

    elif evidence.breath_type is EnsembleBreathType.COLLECTIVE_RELEASE:
        if role == "lay_out":
            add(
                "collective_release_space",
                0.09 * weight,
                "collective release can remain unfilled",
            )
        if action == "sustained_support":
            add(
                "collective_release_sustain",
                -0.06 * weight,
                "sustained harmony can erase a collective release",
            )

    return BebopBreathCompingBias(score, components, tuple(reasons))
