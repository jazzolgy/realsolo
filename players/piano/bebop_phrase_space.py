"""Phrase-space evidence for bebop piano solo interaction.

This layer represents ensemble activity changes without assigning the cause to a
specific player unless attribution evidence exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PhraseSpaceType(str, Enum):
    NONE = "none"
    QUIET_ACTIVE = "quiet_active"
    DEEP_RELEASE = "deep_release"


@dataclass(frozen=True)
class BebopPhraseSpaceEvidence:
    space_type: PhraseSpaceType = PhraseSpaceType.NONE
    energy_drop: float = 0.0
    attack_persistence: float = 0.0
    reentry_contrast: float = 0.0
    confidence: float = 0.0
    actor_attribution_confidence: float = 0.0

    def validate(self) -> None:
        for name in (
            "energy_drop",
            "attack_persistence",
            "reentry_contrast",
            "confidence",
            "actor_attribution_confidence",
        ):
            value=getattr(self,name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


def classify_phrase_space(
    *,
    energy_ratio_to_context: float,
    attack_ratio_to_context: float,
    reentry_ratio: float,
    confidence: float = 0.8,
) -> BebopPhraseSpaceEvidence:
    """Classify a local activity reduction without claiming who caused it."""
    energy_drop=max(0.0,min(1.0,1.0-energy_ratio_to_context))
    attack_persistence=max(0.0,min(1.0,attack_ratio_to_context))
    reentry_contrast=max(0.0,min(1.0,reentry_ratio-1.0))

    if energy_drop >= 0.60 and attack_persistence <= 0.75:
        space_type=PhraseSpaceType.DEEP_RELEASE
    elif energy_drop >= 0.30:
        space_type=PhraseSpaceType.QUIET_ACTIVE
    else:
        space_type=PhraseSpaceType.NONE

    result=BebopPhraseSpaceEvidence(
        space_type=space_type,
        energy_drop=energy_drop,
        attack_persistence=attack_persistence,
        reentry_contrast=reentry_contrast,
        confidence=max(0.0,min(1.0,confidence)),
        actor_attribution_confidence=0.0,
    )
    result.validate()
    return result
