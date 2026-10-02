"""Piano-specific realization of shared semantic solo candidates."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.legend_style_core import CandidateEvent
from music_intelligence.reasoning.solo_candidates import SoloCandidateSpec
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent
from .solo_expression import PianoSoloExpression,realize_piano_solo_expression

@dataclass(frozen=True)
class PianoSoloRealizerContext:
    low_midi:int=48
    high_midi:int=96
    anchor_midi:int=72
    hand:str="RH"
    previous_pitch_midi:int|None=None
    def validate(self)->None:
        if not 21<=self.low_midi<self.high_midi<=108: raise ValueError("invalid piano solo register")
        if self.hand not in {"LH","RH"}: raise ValueError("hand must be LH or RH")

@dataclass(frozen=True)
class PianoSoloRealization:
    event:CandidateEvent
    hand:str
    expression:PianoSoloExpression

def _nearest(pc:int,ctx:PianoSoloRealizerContext)->int:
    pitches=[n for n in range(ctx.low_midi,ctx.high_midi+1) if n%12==pc]
    if not pitches: raise ValueError("pitch class unavailable in piano register")
    anchor=ctx.previous_pitch_midi if ctx.previous_pitch_midi is not None else ctx.anchor_midi
    return min(pitches,key=lambda n:(abs(n-anchor),n))

class PianoSoloRealizer:
    def realize(self,candidate:SoloCandidateSpec,expression:SoloExpressionIntent,context:PianoSoloRealizerContext)->PianoSoloRealization:
        candidate.validate(); expression.validate(); context.validate()
        px=realize_piano_solo_expression(expression)
        pitch=None if candidate.pitch_class is None else _nearest(candidate.pitch_class,context)
        event=CandidateEvent(
            pitch,
            candidate.duration_beats*px.sustain_ratio,
            onset_offset_beats=candidate.onset_offset_beats+px.timing_offset_beats,
            tags=frozenset(set(candidate.tags)|set(px.tags)|{"piano_solo",f"hand:{context.hand}",f"touch:{px.touch}",f"pedal:{px.pedal}"}),
            source_family=f"piano:{candidate.source_family}",
        )
        return PianoSoloRealization(event,context.hand,px)
