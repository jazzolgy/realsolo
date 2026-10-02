"""Instrument-neutral current harmonic/form turn context."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from music_intelligence.harmony.jazz_harmony_core import HarmonicFrame,HarmonicIntent
from music_intelligence.harmony.orchestrator import HarmonicReasoningResult
from .turn_taking import TurnTakingEvidence,TurnTakingType

class HarmonicTurnPhase(str, Enum):
    STABLE_FIELD="stable_field"
    DIRECTED_RESOLUTION="directed_resolution"
    ANTICIPATORY="anticipatory"
    FORM_BOUNDARY="form_boundary"
    AMBIGUOUS="ambiguous"

@dataclass(frozen=True)
class HarmonicTurnContext:
    phase:HarmonicTurnPhase=HarmonicTurnPhase.AMBIGUOUS
    turn_type:TurnTakingType=TurnTakingType.AMBIGUOUS
    phrase_boundary_pressure:float=0.
    anticipation_strength:float=0.
    resolution_strength:float=0.
    stability_strength:float=0.
    confidence:float=0.
    def validate(self)->None:
        for name in ("phrase_boundary_pressure","anticipation_strength","resolution_strength","stability_strength","confidence"):
            v=getattr(self,name)
            if not 0.<=v<=1.: raise ValueError(f"{name} must be within 0..1")

def _function_text(frame:HarmonicFrame)->str:
    return " ".join(ev.function.lower() for ev in (frame.inferred,frame.observed,frame.expected) if ev is not None and ev.function)

def derive_harmonic_turn_context(frame:HarmonicFrame,turn:TurnTakingEvidence,reasoning:HarmonicReasoningResult|None=None)->HarmonicTurnContext:
    frame.validate(); turn.validate()
    boundary=max(0.,min(1.,(frame.phrase_position-.72)/.28))
    if (frame.cadence_state or "open").lower() not in {"open","none",""}: boundary=max(boundary,.55)
    funcs=_function_text(frame); dominant="dominant" in funcs or funcs.strip() in {"v","v7"}
    anticipation=.65 if frame.next_expected is not None else 0.
    resolution=.75 if dominant else 0.
    stability=0.
    if reasoning is not None:
        for option in reasoning.action_options:
            strength=max(0.,min(1.,option.confidence*option.interpretation_compatibility))
            if option.intent is HarmonicIntent.ANTICIPATE: anticipation=max(anticipation,strength)
            elif option.intent in {HarmonicIntent.CONNECT,HarmonicIntent.STABILIZE}: resolution=max(resolution,.75*strength)
            elif option.intent in {HarmonicIntent.COLOR,HarmonicIntent.DELAY_RESOLUTION}: stability=max(stability,.65*strength)
    if not dominant and frame.tension<=.4: stability=max(stability,.60)
    phase=(HarmonicTurnPhase.FORM_BOUNDARY if boundary>=.65 else HarmonicTurnPhase.ANTICIPATORY if anticipation>=.65 else HarmonicTurnPhase.DIRECTED_RESOLUTION if resolution>=.65 else HarmonicTurnPhase.STABLE_FIELD if stability>=.55 else HarmonicTurnPhase.AMBIGUOUS)
    confidence=min(1.,.45*turn.confidence+.20*boundary+.15*anticipation+.15*resolution+.05*stability)
    out=HarmonicTurnContext(phase,turn.episode_type,boundary,anticipation,resolution,stability,confidence); out.validate(); return out
