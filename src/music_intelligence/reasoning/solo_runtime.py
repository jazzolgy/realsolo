"""Instrument-neutral online solo tick planning."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.harmony.jazz_harmony_core import HarmonicFrame
from music_intelligence.harmony.scale_linear_core import build_linear_connection_affordances
from .ensemble_complementarity import EnsembleComplementarityEvidence
from .harmonic_turn import HarmonicTurnContext
from .solo_candidates import SoloCandidateSpec,generate_solo_candidate_specs
from .solo_phrase_intent import SoloPhraseIntent,derive_solo_phrase_intent
from .turn_taking import TurnTakingEvidence

@dataclass(frozen=True)
class SoloTickPlan:
    intent:SoloPhraseIntent
    candidates:tuple[SoloCandidateSpec,...]
    def validate(self)->None:
        self.intent.validate()
        if not self.candidates: raise ValueError("solo tick must contain immediate candidates")
        for c in self.candidates:
            c.validate()
            if hasattr(c,"future_notes") or hasattr(c,"phrase_sequence"): raise ValueError("future phrase data is not allowed")

def build_solo_tick(*,harmonic_frame:HarmonicFrame,harmonic_turn:HarmonicTurnContext,turn:TurnTakingEvidence,complementarity:EnsembleComplementarityEvidence,current_pitch_class:int|None=None,target_pitch_classes:frozenset[int]=frozenset(),local_key_pitch_classes:frozenset[int]=frozenset(),structural_pitch_classes:frozenset[int]=frozenset(),duration_beats:float=.5)->SoloTickPlan:
    intent=derive_solo_phrase_intent(harmonic_turn,turn,complementarity)
    linear=build_linear_connection_affordances(harmonic_frame,current_pitch_class=current_pitch_class,target_pitch_classes=target_pitch_classes,local_key_pitch_classes=local_key_pitch_classes)
    specs=generate_solo_candidate_specs(intent=intent,linear_affordances=linear,structural_pitch_classes=structural_pitch_classes,duration_beats=duration_beats)
    plan=SoloTickPlan(intent,specs); plan.validate(); return plan
