"""Piano realization of shared solo-expression intent."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent

@dataclass(frozen=True)
class PianoSoloExpression:
    velocity:int
    touch:str="neutral"
    pedal:str="none"
    timing_offset_beats:float=0.0
    sustain_ratio:float=1.0
    tags:frozenset[str]=frozenset()

def realize_piano_solo_expression(intent:SoloExpressionIntent)->PianoSoloExpression:
    intent.validate()
    velocity=max(1,min(127,int(round(42+70*intent.dynamic_energy+12*(intent.accent-.5)))))
    tags=set(intent.articulation_tags)
    touch="percussive" if intent.accent>=.7 else "legato" if intent.sustain_ratio>=1.1 else "neutral"
    pedal="half" if intent.sustain_ratio>=1.15 and "tension_clarity" not in tags else "none"
    return PianoSoloExpression(
        velocity=velocity,
        touch=touch,
        pedal=pedal,
        timing_offset_beats=intent.timing_offset_beats,
        sustain_ratio=intent.sustain_ratio,
        tags=frozenset(tags),
    )
