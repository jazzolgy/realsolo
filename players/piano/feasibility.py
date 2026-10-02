"""Piano-specific feasibility behind the shared feasibility contract."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.feasibility import FeasibilityAssessment
from .solo_realizer import PianoSoloRealization

@dataclass(frozen=True)
class PianoFeasibilityContext:
    previous_pitch_midi:int|None=None
    comfortable_leap_semitones:int=7
    low_midi:int=21
    high_midi:int=108

def assess_piano_solo_feasibility(realization:PianoSoloRealization,context:PianoFeasibilityContext=PianoFeasibilityContext())->FeasibilityAssessment:
    pitch=realization.event.pitch_midi
    if pitch is None:
        out=FeasibilityAssessment(True,confidence=1.0,reasons=("intentional space",)); out.validate(); return out
    if not context.low_midi<=pitch<=context.high_midi:
        out=FeasibilityAssessment(False,1.0,physical_conflict=1.0,reasons=("outside piano range",)); out.validate(); return out
    leap=abs(pitch-context.previous_pitch_midi) if context.previous_pitch_midi is not None else 0
    transition=min(1.0,max(0,leap-context.comfortable_leap_semitones)/12.0)
    reasons=() if transition==0 else ("large register transition",)
    out=FeasibilityAssessment(True,cost=.55*transition,transition_cost=transition,confidence=1.0,reasons=reasons)
    out.validate(); return out

def assess_piano_polyphonic_feasibility(candidate,ensemble_activity:float=.5)->FeasibilityAssessment:
    candidate.validate()
    pitches=candidate.event.pitches_midi
    span=max(pitches)-min(pitches) if pitches else 0
    cost=0.0; conflict=0.0; reasons=[]
    if span>36 and not candidate.hand_assignment:
        cost+=.35; conflict=max(conflict,.35); reasons.append("wide span without hand assignment")
    hands=dict(candidate.hand_assignment)
    if hands:
        by_id={v.voice_id:v.pitch_midi for v in candidate.event.voices}
        lh=[by_id[v] for v,h in hands.items() if h=="LH"]; rh=[by_id[v] for v,h in hands.items() if h=="RH"]
        if lh and rh and max(lh)>min(rh)+7:
            cost+=.3; conflict=max(conflict,.3); reasons.append("hand crossing pressure")
    if candidate.pedal in {"sustain","half"} and ensemble_activity>=.8 and "dense" in candidate.event.tags:
        cost+=.2; reasons.append("dense pedal texture in active ensemble")
    out=FeasibilityAssessment(True,min(1.,cost),physical_conflict=min(1.,conflict),reasons=tuple(reasons))
    out.validate(); return out
