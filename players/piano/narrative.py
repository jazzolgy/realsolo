"""Immediate narrative bias for piano comping.

This module changes only current-candidate weights. It never schedules or freezes a
future sequence of voicing families.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .comping import InteractionRole, PianoCompingCandidate
from .interaction import EnergyDirection, PianoInteractionState


@dataclass(frozen=True)
class NarrativeBiasScore:
    total: float
    components: Mapping[str, float]
    reasons: tuple[str, ...]


def evaluate_narrative_bias(
    candidate: PianoCompingCandidate,
    interaction: PianoInteractionState,
) -> NarrativeBiasScore:
    interaction.validate()
    score = 0.0
    components: dict[str, float] = {}
    reasons: list[str] = []

    family_tags = set(candidate.tags)
    if candidate.realization is not None:
        family_tags |= set(candidate.realization.event.tags)

    def add(key: str, value: float, reason: str) -> None:
        nonlocal score
        score += value
        components[key] = components.get(key, 0.0) + value
        reasons.append(reason)

    if interaction.energy_direction is EnergyDirection.UP:
        if candidate.role is InteractionRole.BUILD:
            add("energy_role_fit", 0.12, "build role matches rising energy")
        if {"quartal", "inverted_quartal", "mixed"} & family_tags:
            add("expansive_family_fit", 0.08, "expanded voicing family supports rising energy")
        if candidate.role is InteractionRole.LAY_OUT and interaction.soloist_activity < 0.45:
            add("premature_release", -0.05, "laying out may undercut an available build")

    elif interaction.energy_direction is EnergyDirection.DOWN:
        if candidate.role in {InteractionRole.RELEASE, InteractionRole.LAY_OUT}:
            add("energy_role_fit", 0.12, "release/lay-out matches falling energy")
        if "shell" in family_tags or "sparse" in family_tags:
            add("reduced_weight_fit", 0.08, "sparse voicing supports falling energy")
        if candidate.role is InteractionRole.BUILD:
            add("build_against_release", -0.10, "build role conflicts with falling energy")

    else:
        if candidate.role in {InteractionRole.SUPPORT, InteractionRole.ANCHOR}:
            add("stable_role_fit", 0.05, "support/anchor fits stable energy")

    intrusion = interaction.recent_piano_density.intrusion_index
    if intrusion >= 0.60:
        if candidate.role is InteractionRole.LAY_OUT:
            add("density_recovery", 0.10, "recent piano density favors recovery space")
        elif "dense" in family_tags or candidate.role is InteractionRole.BUILD:
            add("density_accumulation", -0.08, "recent density argues against further weight")

    if interaction.phrase_space is not None and interaction.phrase_space.usable:
        if candidate.role in {
            InteractionRole.ANSWER,
            InteractionRole.FILL,
            InteractionRole.PUNCTUATE,
        }:
            add("phrase_space_fit", 0.08, "candidate uses a high-confidence phrase-space window")

    return NarrativeBiasScore(score, components, tuple(reasons))
