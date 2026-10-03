"""Sax-specific realization of shared semantic solo candidates."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.legend_style_core import CandidateEvent
from music_intelligence.reasoning.solo_candidates import SoloCandidateSpec
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent
from .solo_expression import SaxSoloExpression,realize_sax_solo_expression

@dataclass(frozen=True)
class SaxSoloRealizerContext:
    low_midi:int=50
    high_midi:int=94
    anchor_midi:int=67
    previous_pitch_midi:int|None=None
    def validate(self)->None:
        if not 0<=self.low_midi<self.high_midi<=127: raise ValueError("invalid sax register")

@dataclass(frozen=True)
class SaxSoloRealization:
    event:CandidateEvent
    expression:SaxSoloExpression

def _nearest(pc:int,ctx:SaxSoloRealizerContext)->int:
    xs=[n for n in range(ctx.low_midi,ctx.high_midi+1) if n%12==pc]
    if not xs: raise ValueError("pitch class unavailable in sax register")
    anchor=ctx.previous_pitch_midi if ctx.previous_pitch_midi is not None else ctx.anchor_midi
    return min(xs,key=lambda n:(abs(n-anchor),n))

class SaxSoloRealizer:
    def realize(self,candidate:SoloCandidateSpec,expression:SoloExpressionIntent,context:SaxSoloRealizerContext)->SaxSoloRealization:
        candidate.validate(); expression.validate(); context.validate()
        sx=realize_sax_solo_expression(expression)
        pitch=None if candidate.pitch_class is None else _nearest(candidate.pitch_class,context)
        event=CandidateEvent(
            pitch,candidate.duration_beats*sx.sustain_ratio,
            onset_offset_beats=candidate.onset_offset_beats+sx.timing_offset_beats,
            tags=frozenset(set(candidate.tags)|set(sx.articulation_tags)|{"sax_solo"}),
            source_family=f"sax:{candidate.source_family}",
        )
        return SaxSoloRealization(event,sx)
