"""Instrument-neutral observed turn-taking evidence."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class TurnTakingType(str, Enum):
    SUPPORTED_HANDOFF_REENTRY = "supported_handoff_reentry"
    COLLECTIVE_RELEASE_REENTRY = "collective_release_reentry"
    FOREGROUND_CONTINUES = "foreground_continues"
    AMBIGUOUS = "ambiguous"

@dataclass(frozen=True)
class TurnTakingEvidence:
    episode_type: TurnTakingType = TurnTakingType.AMBIGUOUS
    foreground_handoff_ratio: float = 1.0
    low_harmonic_support_ratio: float = 1.0
    attack_support_ratio: float = 1.0
    reentry_strength: float = 1.0
    confidence: float = 0.0
    actor_attribution_confidence: float = 0.0

    def validate(self) -> None:
        for name in ("foreground_handoff_ratio","low_harmonic_support_ratio","attack_support_ratio","reentry_strength","confidence","actor_attribution_confidence"):
            value=getattr(self,name)
            if value < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.confidence > 1 or self.actor_attribution_confidence > 1:
            raise ValueError("confidence values must be within 0..1")

def classify_turn_taking(*,foreground_during_pre:float,low_support_during_pre:float,attack_support_during_pre:float,foreground_post_during:float,confidence:float=.75)->TurnTakingEvidence:
    support=max(low_support_during_pre,attack_support_during_pre)
    if foreground_during_pre<=.40 and support>=.60 and foreground_post_during>=2.0:
        kind=TurnTakingType.SUPPORTED_HANDOFF_REENTRY
    elif foreground_during_pre<=.40 and low_support_during_pre<=.55 and attack_support_during_pre<=.70 and foreground_post_during>=2.0:
        kind=TurnTakingType.COLLECTIVE_RELEASE_REENTRY
    elif foreground_during_pre>=1.20:
        kind=TurnTakingType.FOREGROUND_CONTINUES
    else:
        kind=TurnTakingType.AMBIGUOUS
    out=TurnTakingEvidence(kind,max(0.,foreground_during_pre),max(0.,low_support_during_pre),max(0.,attack_support_during_pre),max(0.,foreground_post_during),max(0.,min(1.,confidence)),0.)
    out.validate()
    return out
