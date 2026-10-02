"""Observed foreground/support complementarity for bebop interaction.

This representation describes activity relations in a mixed ensemble signal.
It does not identify a specific instrument as the cause unless separate evidence exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EnsembleBreathType(str, Enum):
    NONE = "none"
    FOREGROUND_HANDOFF = "foreground_handoff"
    COLLECTIVE_RELEASE = "collective_release"
    COLLECTIVE_BUILD = "collective_build"


class SupportCarryMode(str, Enum):
    HARMONIC_CARRIED = "harmonic_carried"
    PERCUSSIVE_CARRIED = "percussive_carried"
    MIXED_SUPPORT = "mixed_support"
    MODERATE_SUPPORT = "moderate_support"
    UNSPECIFIED = "unspecified"


@dataclass(frozen=True)
class EnsembleComplementarityEvidence:
    breath_type: EnsembleBreathType = EnsembleBreathType.NONE
    foreground_drop: float = 0.0
    low_harmonic_support: float = 0.0
    percussive_support: float = 0.0
    post_foreground_reentry: float = 0.0
    confidence: float = 0.0
    actor_attribution_confidence: float = 0.0

    def validate(self) -> None:
        for name in (
            "foreground_drop",
            "low_harmonic_support",
            "percussive_support",
            "post_foreground_reentry",
            "confidence",
            "actor_attribution_confidence",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


def classify_ensemble_complementarity(
    *,
    foreground_ratio: float,
    low_harmonic_support_ratio: float,
    percussive_support_ratio: float,
    post_foreground_ratio: float,
    confidence: float = 0.75,
) -> EnsembleComplementarityEvidence:
    foreground_drop = max(0.0, min(1.0, 1.0 - foreground_ratio))
    low_support = max(0.0, min(1.0, low_harmonic_support_ratio))
    perc_support = max(0.0, min(1.0, percussive_support_ratio))
    post_reentry = max(0.0, min(1.0, (post_foreground_ratio - 1.0) / 3.0))

    support = max(low_support, perc_support)

    if foreground_drop >= 0.55 and support >= 0.75:
        breath_type = EnsembleBreathType.FOREGROUND_HANDOFF
    elif foreground_drop >= 0.55 and low_support <= 0.55 and perc_support <= 0.70:
        breath_type = EnsembleBreathType.COLLECTIVE_RELEASE
    elif foreground_ratio >= 1.25 and support >= 0.9:
        breath_type = EnsembleBreathType.COLLECTIVE_BUILD
    else:
        breath_type = EnsembleBreathType.NONE

    result = EnsembleComplementarityEvidence(
        breath_type=breath_type,
        foreground_drop=foreground_drop,
        low_harmonic_support=low_support,
        percussive_support=perc_support,
        post_foreground_reentry=post_reentry,
        confidence=max(0.0, min(1.0, confidence)),
        actor_attribution_confidence=0.0,
    )
    result.validate()
    return result



def support_carry_mode(
    evidence: EnsembleComplementarityEvidence,
) -> SupportCarryMode:
    """Describe which accompaniment layer most clearly carries a handoff."""
    evidence.validate()
    low=evidence.low_harmonic_support
    perc=evidence.percussive_support

    if low >= 0.8 and perc >= 0.8:
        return SupportCarryMode.MIXED_SUPPORT
    if low >= 0.8 and perc < 0.8:
        return SupportCarryMode.HARMONIC_CARRIED
    if perc >= 0.8 and low < 0.8:
        return SupportCarryMode.PERCUSSIVE_CARRIED
    if max(low,perc) >= 0.55:
        return SupportCarryMode.MODERATE_SUPPORT
    return SupportCarryMode.UNSPECIFIED
