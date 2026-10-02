"""Drum-specific realization of shared semantic solo candidates.

Pitch-class material is optional for drums. Rhythm/phrase/expression dimensions
may transfer from any source while orchestration is owned by the Drum Player.
"""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.solo_candidates import SoloCandidateSpec
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent
from music_intelligence.reasoning.groove_context import GrooveTemporalContext, groove_timing_offset_beats
from .model import DrumGesture,DrumHit,DrumVoice,GestureRole,Limb
from .solo_expression import DrumSoloExpression,realize_drum_solo_expression

@dataclass(frozen=True)
class DrumSoloRealizerContext:
    tempo_bpm:float=140.0
    primary_voice:DrumVoice=DrumVoice.SNARE
    primary_limb:Limb=Limb.LEFT_HAND
    role:GestureRole=GestureRole.FILL
    beat_position_beats:float=0.0
    groove:GrooveTemporalContext|None=None

@dataclass(frozen=True)
class DrumSoloRealization:
    gesture:DrumGesture
    expression:DrumSoloExpression

class DrumSoloRealizer:
    def realize(self,candidate:SoloCandidateSpec,expression:SoloExpressionIntent,context:DrumSoloRealizerContext)->DrumSoloRealization:
        candidate.validate(); expression.validate()
        if context.groove is not None: context.groove.validate()
        dx=realize_drum_solo_expression(expression,context.tempo_bpm)
        groove_offset_beats=groove_timing_offset_beats(context.beat_position_beats+candidate.onset_offset_beats,context.groove)
        groove_ms=groove_offset_beats*(60000.0/context.tempo_bpm)
        groove_tag=f"groove:{context.groove.feel.value}" if context.groove is not None else "groove:player_default"
        if candidate.pitch_class is None and "rest" in candidate.tags:
            gesture=DrumGesture(hits=(),role=GestureRole.SPACE,tags=frozenset(set(candidate.tags)|{"drum_solo","space",groove_tag}),provenance=("shared_solo_candidate","drum_realizer"))
        else:
            hit=DrumHit(context.primary_voice,context.primary_limb,dx.velocity,dx.microtiming_ms+groove_ms,dx.articulation)
            gesture=DrumGesture(hits=(hit,),role=context.role,tags=frozenset(set(candidate.tags)|{"drum_solo",groove_tag}),provenance=("shared_solo_candidate","drum_realizer"))
        gesture.validate()
        return DrumSoloRealization(gesture,dx)
