"""Sax realization of shared solo-expression intent."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent

@dataclass(frozen=True)
class SaxSoloExpression:
    velocity:int
    articulation_tags:tuple[str,...]
    timing_offset_beats:float=0.0
    sustain_ratio:float=1.0

def realize_sax_solo_expression(intent:SoloExpressionIntent)->SaxSoloExpression:
    intent.validate()
    velocity=max(1,min(127,int(round(44+68*intent.dynamic_energy+10*(intent.accent-.5)))))
    tags=list(intent.articulation_tags)
    if intent.accent>=.7: tags.append("accent")
    if intent.sustain_ratio>=1.1: tags.append("sustain")
    if not tags: tags.append("neutral")
    return SaxSoloExpression(velocity,tuple(dict.fromkeys(tags)),intent.timing_offset_beats,intent.sustain_ratio)
