"""Bass-specific feasibility implementing the shared assessment schema."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.feasibility import FeasibilityAssessment
from .solo_realizer import BassSoloRealization

@dataclass(frozen=True)
class BassFeasibilityContext:
    low_midi:int=28
    high_midi:int=67
    previous_pitch_midi:int|None=None
    comfortable_leap_semitones:int=7

def assess_bass_solo_feasibility(realization:BassSoloRealization,context:BassFeasibilityContext=BassFeasibilityContext())->FeasibilityAssessment:
    pitch=realization.event.pitch_midi
    if pitch is None:
        out=FeasibilityAssessment(True,reasons=("intentional bass space",)); out.validate(); return out
    if not context.low_midi<=pitch<=context.high_midi:
        out=FeasibilityAssessment(False,1.0,physical_conflict=1.0,reasons=("outside bass range",)); out.validate(); return out
    leap=abs(pitch-context.previous_pitch_midi) if context.previous_pitch_midi is not None else 0
    transition=min(1.,max(0,leap-context.comfortable_leap_semitones)/12.)
    out=FeasibilityAssessment(True,.6*transition,transition_cost=transition,reasons=(() if transition==0 else ("large position/register transition",)))
    out.validate(); return out
