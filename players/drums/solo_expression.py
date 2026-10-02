"""Drum-set realization of shared solo-expression intent."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent

@dataclass(frozen=True)
class DrumSoloExpression:
    velocity:int
    articulation:str
    microtiming_ms:float
    accent:float

def realize_drum_solo_expression(intent:SoloExpressionIntent,tempo_bpm:float)->DrumSoloExpression:
    intent.validate()
    if not 30<=tempo_bpm<=360: raise ValueError("tempo_bpm outside supported range")
    velocity=max(1,min(127,int(round(42+68*intent.dynamic_energy+14*(intent.accent-.5)))))
    articulation="accent" if intent.accent>=.7 else "sustain" if intent.sustain_ratio>=1.1 else "neutral"
    micro=intent.timing_offset_beats*(60000.0/tempo_bpm)
    return DrumSoloExpression(velocity,articulation,micro,intent.accent)
