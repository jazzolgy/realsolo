"""Instrument-neutral solo-expression intention.

This layer says *what expressive behavior is intended*. Instrument-specific
Players decide how to realize it physically.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SoloExpressionIntent:
    dynamic_energy: float = 0.5
    accent: float = 0.5
    sustain_ratio: float = 1.0
    timing_offset_beats: float = 0.0
    articulation_tags: frozenset[str] = frozenset()
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        for name in ("dynamic_energy", "accent", "confidence"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if not 0.0 <= self.sustain_ratio <= 2.0:
            raise ValueError("sustain_ratio must be within 0..2")
        if not -1.0 <= self.timing_offset_beats <= 1.0:
            raise ValueError("timing_offset_beats must remain a local adjustment")


def expression_from_solo_context(
    *,
    tension: float = 0.0,
    phrase_maturity: float = 0.0,
    ensemble_activity: float = 0.5,
    release: bool = False,
    accent_requested: bool = False,
) -> SoloExpressionIntent:
    for name, value in (
        ("tension", tension),
        ("phrase_maturity", phrase_maturity),
        ("ensemble_activity", ensemble_activity),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be within 0..1")

    energy = max(0.15, min(0.9, 0.42 + 0.28 * tension - 0.16 * ensemble_activity))
    accent = max(0.2, min(0.9, 0.42 + (0.22 if accent_requested else 0.0) + 0.12 * tension))
    sustain = 1.0
    tags: set[str] = set()

    if release or phrase_maturity >= 0.85:
        energy *= 0.82
        sustain = 1.12
        tags.add("phrase_release")
    if tension >= 0.75:
        tags.add("tension_clarity")
    if ensemble_activity >= 0.75:
        tags.add("ensemble_space_sensitive")

    out = SoloExpressionIntent(
        dynamic_energy=energy,
        accent=accent,
        sustain_ratio=sustain,
        articulation_tags=frozenset(tags),
        provenance=("shared_solo_expression",),
    )
    out.validate()
    return out
