"""Drum-specific realization of shared semantic solo candidates.

Pitch-class material is optional for drums. Rhythm/phrase/expression dimensions
may transfer from any source while orchestration is owned by the Drum Player.
"""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.solo_candidates import SoloCandidateSpec
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent
from .model import DrumGesture,DrumHit,DrumVoice,GestureRole,Limb
from .solo_expression import DrumSoloExpression,realize_drum_solo_expression

@dataclass(frozen=True)
class DrumSoloRealizerContext:
    tempo_bpm:float=140.0
    primary_voice:DrumVoice=DrumVoice.SNARE
    primary_limb:Limb=Limb.LEFT_HAND
    role:GestureRole=GestureRole.FILL

@dataclass(frozen=True)
class DrumSoloRealization:
    gesture:DrumGesture
    expression:DrumSoloExpression

class DrumSoloRealizer:
    def realize(self,candidate:SoloCandidateSpec,expression:SoloExpressionIntent,context:DrumSoloRealizerContext)->DrumSoloRealization:
        candidate.validate(); expression.validate()
        dx=realize_drum_solo_expression(expression,context.tempo_bpm)
        if candidate.pitch_class is None and "rest" in candidate.tags:
            gesture=DrumGesture(hits=(),role=GestureRole.SPACE,tags=frozenset(set(candidate.tags)|{"drum_solo","space"}),provenance=("shared_solo_candidate","drum_realizer"))
        else:
            hit=DrumHit(context.primary_voice,context.primary_limb,dx.velocity,dx.microtiming_ms,dx.articulation)
            gesture=DrumGesture(hits=(hit,),role=context.role,tags=frozenset(set(candidate.tags)|{"drum_solo"}),provenance=("shared_solo_candidate","drum_realizer"))
        gesture.validate()
        return DrumSoloRealization(gesture,dx)
