"""Core-facing semantic tags for piano harmonic realizations.

The adapter exposes meaning already present in resolved harmonic roles and piano
family labels. It never parses chord symbols or invents harmonic functions.
"""
from __future__ import annotations

from dataclasses import replace

from .policy import PianoRealizationCandidate


def harmonic_semantic_tags(realization: PianoRealizationCandidate) -> frozenset[str]:
    event = realization.event
    family = event.source_family.removeprefix("piano_")
    tags: set[str] = set()

    if family == "shell":
        tags |= {"guide_tone", "harmonic_identity", "voice_leading"}
    elif family == "rootless":
        tags |= {"guide_tone", "extension", "color_tone", "voice_leading"}
    elif family in {"quartal", "inverted_quartal"}:
        tags |= {"quartal_color", "modal_color", "color_tone"}
    elif family == "tertian":
        tags |= {"harmonic_identity", "voice_leading"}
    elif family == "mixed":
        tags |= {"extension", "color_tone"}
    elif family == "octave":
        tags |= {"harmonic_identity"}

    roles = {str(v.harmonic_role or "").lower() for v in event.voices}
    if roles & {"3rd", "b3", "minor_3rd"}:
        tags |= {"third", "guide_tone"}
    if roles & {"7th", "b7", "major_7th", "minor_7th"}:
        tags |= {"seventh", "guide_tone"}
    if "root" in roles:
        tags.add("root")

    extensions = {"9th","9","b9","#9","11th","11","#11","13th","13","b13"}
    if roles & extensions:
        tags |= {"extension", "color_tone", "tension"}
    if roles & {"b9","#9","b13","#11"}:
        tags |= {"altered", "high_tension"}
    if "#9" in roles:
        tags.add("sharp9")
    if "b9" in roles:
        tags.add("b9")
    if "b13" in roles:
        tags.add("b13")

    return frozenset(tags)


def annotate_harmonic_semantics(
    realization: PianoRealizationCandidate,
) -> PianoRealizationCandidate:
    """Return the same realization with additive Core-facing semantic tags."""
    event = realization.event
    semantic = harmonic_semantic_tags(realization)
    return replace(
        realization,
        event=replace(event, tags=frozenset(set(event.tags) | set(semantic))),
    )