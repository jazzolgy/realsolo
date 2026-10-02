"""Bass realization of shared solo-expression intent."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent

@dataclass(frozen=True)
class BassSoloExpression:
    velocity:int
    sounding_length_ratio:float
    articulation:str
    timing_offset_beats:float=0.0

def realize_bass_solo_expression(intent:SoloExpressionIntent)->BassSoloExpression:
    intent.validate()
    velocity=max(1,min(127,int(round(46+62*intent.dynamic_energy+10*(intent.accent-.5)))))
    articulation="accented" if intent.accent>=.7 else "connected" if intent.sustain_ratio>=1.05 else "neutral"
    return BassSoloExpression(velocity,min(1.4,max(.25,intent.sustain_ratio)),articulation,intent.timing_offset_beats)
