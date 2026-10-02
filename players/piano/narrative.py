"""Immediate narrative bias for piano comping.

This module changes only current-candidate weights. It never schedules or freezes a
future sequence of voicing families.

It intentionally avoids importing the comping module at runtime so the narrative
layer remains a lightweight evaluator rather than creating a circular dependency.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .interaction import EnergyDirection, PianoInteractionState


@dataclass(frozen=True)
class NarrativeBiasScore:
    total: float
    components: Mapping[str, float]
    reasons: tuple[str, ...]


def _role_value(candidate: Any) -> str:
    role = getattr(candidate, "role", None)
    return getattr(role, "value", str(role) if role is not None else "")


def evaluate_narrative_bias(
    candidate: Any,
    interaction: PianoInteractionState,
) -> NarrativeBiasScore:
    interaction.validate()
    score = 0.0
    components: dict[str, float] = {}
    reasons: list[str] = []

    family_tags = set(getattr(candidate, "tags", ()))
    realization = getattr(candidate, "realization", None)
    if realization is not None:
        family_tags |= set(realization.event.tags)

    role = _role_value(candidate)

    def add(key: str, value: float, reason: str) -> None:
        nonlocal score
        score += value
        components[key] = components.get(key, 0.0) + value
        reasons.append(reason)

    if interaction.energy_direction is EnergyDirection.UP:
        if role == "build":
            add("energy_role_fit", 0.12, "build role matches rising energy")
        if {"quartal", "inverted_quartal", "mixed"} & family_tags:
            add("expansive_family_fit", 0.08, "expanded voicing family supports rising energy")
        if role == "lay_out" and interaction.soloist_activity < 0.45:
            add("premature_release", -0.05, "laying out may undercut an available build")

    elif interaction.energy_direction is EnergyDirection.DOWN:
        if role in {"release", "lay_out"}:
            add("energy_role_fit", 0.12, "release/lay-out matches falling energy")
        if "shell" in family_tags or "sparse" in family_tags:
            add("reduced_weight_fit", 0.08, "sparse voicing supports falling energy")
        if role == "build":
            add("build_against_release", -0.10, "build role conflicts with falling energy")

    else:
        if role in {"support", "anchor"}:
            add("stable_role_fit", 0.05, "support/anchor fits stable energy")

    intrusion = interaction.recent_piano_density.intrusion_index
    if intrusion >= 0.60:
        if role == "lay_out":
            add("density_recovery", 0.10, "recent piano density favors recovery space")
        elif "dense" in family_tags or role == "build":
            add("density_accumulation", -0.08, "recent density argues against further weight")

    if interaction.phrase_space is not None and interaction.phrase_space.usable:
        if role in {"answer", "fill", "punctuate"}:
            add("phrase_space_fit", 0.08, "candidate uses a high-confidence phrase-space window")

    return NarrativeBiasScore(score, components, tuple(reasons))
