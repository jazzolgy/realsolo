"""Instrument-neutral foreground/support complementarity."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class EnsembleBreathType(str, Enum):
    NONE="none"
    FOREGROUND_HANDOFF="foreground_handoff"
    COLLECTIVE_RELEASE="collective_release"
    COLLECTIVE_BUILD="collective_build"

class SupportCarryMode(str, Enum):
    HARMONIC_CARRIED="harmonic_carried"
    PERCUSSIVE_CARRIED="percussive_carried"
    MIXED_SUPPORT="mixed_support"
    MODERATE_SUPPORT="moderate_support"
    UNSPECIFIED="unspecified"

@dataclass(frozen=True)
class EnsembleComplementarityEvidence:
    breath_type: EnsembleBreathType=EnsembleBreathType.NONE
    foreground_drop: float=0.
    low_harmonic_support: float=0.
    percussive_support: float=0.
    post_foreground_reentry: float=0.
    confidence: float=0.
    actor_attribution_confidence: float=0.

    def validate(self)->None:
        for name in ("foreground_drop","low_harmonic_support","percussive_support","post_foreground_reentry","confidence","actor_attribution_confidence"):
            value=getattr(self,name)
            if not 0.<=value<=1.:
                raise ValueError(f"{name} must be within 0..1")

def classify_ensemble_complementarity(*,foreground_ratio:float,low_harmonic_support_ratio:float,percussive_support_ratio:float,post_foreground_ratio:float,confidence:float=.75)->EnsembleComplementarityEvidence:
    fd=max(0.,min(1.,1.-foreground_ratio))
    low=max(0.,min(1.,low_harmonic_support_ratio))
    perc=max(0.,min(1.,percussive_support_ratio))
    re=max(0.,min(1.,(post_foreground_ratio-1.)/3.))
    support=max(low,perc)
    if fd>=.55 and support>=.75: kind=EnsembleBreathType.FOREGROUND_HANDOFF
    elif fd>=.55 and low<=.55 and perc<=.70: kind=EnsembleBreathType.COLLECTIVE_RELEASE
    elif foreground_ratio>=1.25 and support>=.9: kind=EnsembleBreathType.COLLECTIVE_BUILD
    else: kind=EnsembleBreathType.NONE
    out=EnsembleComplementarityEvidence(kind,fd,low,perc,re,max(0.,min(1.,confidence)),0.)
    out.validate()
    return out

def support_carry_mode(evidence:EnsembleComplementarityEvidence)->SupportCarryMode:
    evidence.validate(); low=evidence.low_harmonic_support; perc=evidence.percussive_support
    if low>=.8 and perc>=.8:return SupportCarryMode.MIXED_SUPPORT
    if low>=.8:return SupportCarryMode.HARMONIC_CARRIED
    if perc>=.8:return SupportCarryMode.PERCUSSIVE_CARRIED
    if max(low,perc)>=.55:return SupportCarryMode.MODERATE_SUPPORT
    return SupportCarryMode.UNSPECIFIED
