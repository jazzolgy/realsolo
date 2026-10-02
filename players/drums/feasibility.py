"""Drum-set feasibility implementing the shared assessment schema."""
from __future__ import annotations
from music_intelligence.reasoning.feasibility import FeasibilityAssessment
from .physical import limb_can_play
from .solo_realizer import DrumSoloRealization

def assess_drum_solo_feasibility(realization:DrumSoloRealization)->FeasibilityAssessment:
    conflict=0.0; reasons=[]
    for hit in realization.gesture.hits:
        if not limb_can_play(hit.limb,hit.voice):
            conflict=1.0
            reasons.append(f"{hit.limb.value} cannot reach {hit.voice.value}")
    feasible=conflict<1.0
    out=FeasibilityAssessment(feasible,cost=conflict,physical_conflict=conflict,confidence=1.0,reasons=tuple(reasons))
    out.validate(); return out
