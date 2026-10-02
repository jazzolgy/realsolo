"""Observed bebop turn-taking episode morphology.

The classifier summarizes already-observed pre/handoff/post activity. It does not
predict or schedule a future phrase and does not identify the foreground actor unless
separate evidence exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BebopTurnTakingType(str, Enum):
    SUPPORTED_HANDOFF_REENTRY = "supported_handoff_reentry"
    COLLECTIVE_RELEASE_REENTRY = "collective_release_reentry"
    FOREGROUND_CONTINUES = "foreground_continues"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class BebopTurnTakingEvidence:
    episode_type: BebopTurnTakingType
    foreground_handoff_ratio: float
    low_harmonic_support_ratio: float
    attack_support_ratio: float
    reentry_strength: float
    confidence: float = 0.0
    actor_attribution_confidence: float = 0.0

    def validate(self) -> None:
        for name in (
            "foreground_handoff_ratio",
            "low_harmonic_support_ratio",
            "attack_support_ratio",
            "reentry_strength",
            "confidence",
            "actor_attribution_confidence",
        ):
            value=getattr(self,name)
            if value < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.confidence > 1 or self.actor_attribution_confidence > 1:
            raise ValueError("confidence values must be within 0..1")


def classify_bebop_turn_taking(
    *,
    foreground_during_pre: float,
    low_support_during_pre: float,
    attack_support_during_pre: float,
    foreground_post_during: float,
    confidence: float = 0.75,
) -> BebopTurnTakingEvidence:
    """Classify a completed local episode from activity ratios."""
    support=max(low_support_during_pre, attack_support_during_pre)

    if (
        foreground_during_pre <= 0.40
        and support >= 0.60
        and foreground_post_during >= 2.0
    ):
        episode_type=BebopTurnTakingType.SUPPORTED_HANDOFF_REENTRY
    elif (
        foreground_during_pre <= 0.40
        and low_support_during_pre <= 0.55
        and attack_support_during_pre <= 0.70
        and foreground_post_during >= 2.0
    ):
        episode_type=BebopTurnTakingType.COLLECTIVE_RELEASE_REENTRY
    elif foreground_during_pre >= 1.20:
        episode_type=BebopTurnTakingType.FOREGROUND_CONTINUES
    else:
        episode_type=BebopTurnTakingType.AMBIGUOUS

    result=BebopTurnTakingEvidence(
        episode_type=episode_type,
        foreground_handoff_ratio=max(0.0,foreground_during_pre),
        low_harmonic_support_ratio=max(0.0,low_support_during_pre),
        attack_support_ratio=max(0.0,attack_support_during_pre),
        reentry_strength=max(0.0,foreground_post_during),
        confidence=max(0.0,min(1.0,confidence)),
        actor_attribution_confidence=0.0,
    )
    result.validate()
    return result
