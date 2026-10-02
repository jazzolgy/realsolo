"""Bass-specific realization of shared semantic solo candidates."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.legend_style_core import CandidateEvent
from music_intelligence.reasoning.solo_candidates import SoloCandidateSpec
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent
from music_intelligence.reasoning.groove_context import GrooveTemporalContext, groove_timing_offset_beats
from .solo_expression import BassSoloExpression,realize_bass_solo_expression

@dataclass(frozen=True)
class BassSoloRealizerContext:
    low_midi:int=28
    high_midi:int=67
    anchor_midi:int=43
    previous_pitch_midi:int|None=None
    beat_position_beats:float=0.0
    groove:GrooveTemporalContext|None=None
    def validate(self)->None:
        if not 0<=self.low_midi<self.high_midi<=127: raise ValueError("invalid bass register")
        if self.groove is not None: self.groove.validate()

@dataclass(frozen=True)
class BassSoloRealization:
    event:CandidateEvent
    expression:BassSoloExpression

def _nearest(pc:int,ctx:BassSoloRealizerContext)->int:
    xs=[n for n in range(ctx.low_midi,ctx.high_midi+1) if n%12==pc]
    if not xs: raise ValueError("pitch class unavailable in bass register")
    anchor=ctx.previous_pitch_midi if ctx.previous_pitch_midi is not None else ctx.anchor_midi
    return min(xs,key=lambda n:(abs(n-anchor),n))

class BassSoloRealizer:
    def realize(self,candidate:SoloCandidateSpec,expression:SoloExpressionIntent,context:BassSoloRealizerContext)->BassSoloRealization:
        candidate.validate(); expression.validate(); context.validate()
        bx=realize_bass_solo_expression(expression)
        pitch=None if candidate.pitch_class is None else _nearest(candidate.pitch_class,context)
        groove_offset=groove_timing_offset_beats(context.beat_position_beats+candidate.onset_offset_beats,context.groove)
        groove_tag=f"groove:{context.groove.feel.value}" if context.groove is not None else "groove:player_default"
        event=CandidateEvent(
            pitch,candidate.duration_beats*bx.sounding_length_ratio,
            onset_offset_beats=candidate.onset_offset_beats+bx.timing_offset_beats+groove_offset,
            tags=frozenset(set(candidate.tags)|{"bass_solo",groove_tag,f"articulation:{bx.articulation}"}),
            source_family=f"bass:{candidate.source_family}",
        )
        return BassSoloRealization(event,bx)
