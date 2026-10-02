"""Instrument-neutral online solo tick planning."""
from __future__ import annotations
from dataclasses import dataclass, replace
from music_intelligence.harmony.jazz_harmony_core import HarmonicFrame
from music_intelligence.harmony.scale_linear_core import build_linear_connection_affordances
from .ensemble_complementarity import EnsembleComplementarityEvidence
from .harmonic_turn import HarmonicTurnContext
from .solo_candidates import SoloCandidateSpec,generate_solo_candidate_specs
from .solo_phrase_intent import SoloPhraseIntent,derive_solo_phrase_intent
from .turn_taking import TurnTakingEvidence
from .motif import (
    MotifEvaluationContext,
    MotifGenerationContext,
    MotifLearningState,
    MotifMemory,
    MotifPolicyDecision,
    choose_motif_policy,
)

@dataclass(frozen=True)
class SoloTickPlan:
    intent:SoloPhraseIntent
    candidates:tuple[SoloCandidateSpec,...]
    motif_decision:MotifPolicyDecision|None=None
    def validate(self)->None:
        self.intent.validate()
        if not self.candidates: raise ValueError("solo tick must contain immediate candidates")
        for c in self.candidates:
            c.validate()
            if hasattr(c,"future_notes") or hasattr(c,"phrase_sequence"): raise ValueError("future phrase data is not allowed")

def build_solo_tick(*,harmonic_frame:HarmonicFrame,harmonic_turn:HarmonicTurnContext,turn:TurnTakingEvidence,complementarity:EnsembleComplementarityEvidence,current_pitch_class:int|None=None,target_pitch_classes:frozenset[int]=frozenset(),local_key_pitch_classes:frozenset[int]=frozenset(),structural_pitch_classes:frozenset[int]=frozenset(),duration_beats:float=.5,motif_generation_context:MotifGenerationContext|None=None,motif_evaluation_context:MotifEvaluationContext|None=None,motif_memory:MotifMemory|None=None,motif_learning:MotifLearningState=MotifLearningState())->SoloTickPlan:
    intent=derive_solo_phrase_intent(harmonic_turn,turn,complementarity)
    motif_decision=None
    if motif_generation_context is not None:
        motif_decision=choose_motif_policy(
            motif_generation_context,
            motif_evaluation_context or MotifEvaluationContext(),
            memory=motif_memory,
            learning=motif_learning,
        )
        intent=replace(intent,solo_method=motif_decision.development_operation,rationale=intent.rationale+(f"motif:{motif_decision.candidate.identity.motif_id}",))
    linear=build_linear_connection_affordances(harmonic_frame,current_pitch_class=current_pitch_class,target_pitch_classes=target_pitch_classes,local_key_pitch_classes=local_key_pitch_classes)
    specs=generate_solo_candidate_specs(intent=intent,linear_affordances=linear,structural_pitch_classes=structural_pitch_classes,duration_beats=duration_beats)
    if motif_decision is not None:
        motif_tag=f"motif:{motif_decision.candidate.identity.motif_id}"
        specs=tuple(replace(x,tags=frozenset(set(x.tags)|{motif_tag}),source_family=f"motif:{motif_decision.candidate.source_type.value}:{x.source_family}") for x in specs)
    plan=SoloTickPlan(intent,specs,motif_decision); plan.validate(); return plan
