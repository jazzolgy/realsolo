"""Instrument-neutral phrase-space evidence."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class PhraseSpaceType(str, Enum):
    NONE="none"
    QUIET_ACTIVE="quiet_active"
    DEEP_RELEASE="deep_release"

@dataclass(frozen=True)
class PhraseSpaceEvidence:
    space_type: PhraseSpaceType=PhraseSpaceType.NONE
    energy_drop: float=0.
    attack_persistence: float=0.
    reentry_contrast: float=0.
    percussive_support: float=0.
    harmonic_support: float=0.
    confidence: float=0.
    actor_attribution_confidence: float=0.
    def validate(self)->None:
        for name in ("energy_drop","attack_persistence","reentry_contrast","percussive_support","harmonic_support","confidence","actor_attribution_confidence"):
            v=getattr(self,name)
            if not 0.<=v<=1.: raise ValueError(f"{name} must be within 0..1")

def classify_phrase_space(*,energy_ratio_to_context:float,attack_ratio_to_context:float,reentry_ratio:float,percussive_ratio_to_context:float|None=None,harmonic_ratio_to_context:float|None=None,confidence:float=.8)->PhraseSpaceEvidence:
    drop=max(0.,min(1.,1.-energy_ratio_to_context))
    attack=max(0.,min(1.,attack_ratio_to_context))
    re=max(0.,min(1.,reentry_ratio-1.))
    perc=max(0.,min(1.,attack if percussive_ratio_to_context is None else percussive_ratio_to_context))
    harm=max(0.,min(1.,energy_ratio_to_context if harmonic_ratio_to_context is None else harmonic_ratio_to_context))
    kind=PhraseSpaceType.DEEP_RELEASE if drop>=.60 and attack<=.75 else PhraseSpaceType.QUIET_ACTIVE if drop>=.30 else PhraseSpaceType.NONE
    out=PhraseSpaceEvidence(kind,drop,attack,re,perc,harm,max(0.,min(1.,confidence)),0.)
    out.validate(); return out
