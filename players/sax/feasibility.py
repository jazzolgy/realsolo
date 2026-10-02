"""Sax-specific feasibility implementing the shared assessment schema."""
from __future__ import annotations
from music_intelligence.reasoning.feasibility import FeasibilityAssessment
from .physical import SaxPhysicalConstraints,assess_sax_transition
from .solo_realizer import SaxSoloRealization

def assess_sax_solo_feasibility(
    realization:SaxSoloRealization,
    *,
    previous_pitch_midi:int|None,
    notes_since_breath:int,
    beats_since_breath:float,
    constraints:SaxPhysicalConstraints,
)->FeasibilityAssessment:
    pitch=realization.event.pitch_midi
    if pitch is None:
        out=FeasibilityAssessment(True,reasons=("breath/space opportunity",)); out.validate(); return out
    a=assess_sax_transition(
        pitch_midi=pitch,previous_pitch_midi=previous_pitch_midi,
        notes_since_breath=notes_since_breath,beats_since_breath=beats_since_breath,
        constraints=constraints,
    )
    cost=min(1.0,.55*a.transition_cost+.45*a.breath_pressure)
    out=FeasibilityAssessment(a.feasible,cost,a.transition_cost,a.breath_pressure,1.0,a.reasons)
    out.validate(); return out
