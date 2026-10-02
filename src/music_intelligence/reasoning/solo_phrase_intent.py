"""Instrument-neutral short-horizon solo intention."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .online_improviser import SoftPlan
from .solo_grammar import SoloArc,SoloDevelopmentOperation,SoloMethodContext,shared_solo_method_options
from .ensemble_complementarity import EnsembleBreathType,EnsembleComplementarityEvidence
from .harmonic_turn import HarmonicTurnPhase,HarmonicTurnContext
from .turn_taking import TurnTakingEvidence,TurnTakingType

class SoloEntryMode(str,Enum):
    CONTINUE="continue"; PICKUP="pickup"; NEW_PHRASE="new_phrase"; HOLD_SPACE="hold_space"
class SoloTargetMode(str,Enum):
    GUIDE_TONE="guide_tone"; NEXT_HARMONY="next_harmony"; RESOLUTION="resolution"; COLOR="color"; OPEN="open"
class SoloDensityDirection(str,Enum):
    SPARSE="sparse"; STABLE="stable"; BUILD="build"; RELEASE="release"

@dataclass(frozen=True)
class SoloPhraseIntent:
    horizon_beats:float
    entry_mode:SoloEntryMode
    target_mode:SoloTargetMode
    density_direction:SoloDensityDirection
    connector_families:tuple[str,...]
    solo_method:SoloDevelopmentOperation=SoloDevelopmentOperation.STATE
    register_direction:str="stable"
    confidence:float=.5
    rationale:tuple[str,...]=()
    def validate(self)->None:
        if self.horizon_beats<=0: raise ValueError("horizon_beats must be positive")
        if not 0.<=self.confidence<=1.: raise ValueError("confidence must be within 0..1")
    def to_soft_plan(self)->SoftPlan:
        self.validate()
        return SoftPlan(horizon_beats=self.horizon_beats,intention=f"{self.entry_mode.value}:{self.target_mode.value}",soft_targets=(self.target_mode.value,),candidate_families=self.connector_families+(f"solo_method:{self.solo_method.value}",),register_direction=self.register_direction,density_direction=self.density_direction.value,exact_future_notes=())

def derive_solo_phrase_intent(harmonic_turn:HarmonicTurnContext,turn:TurnTakingEvidence,complementarity:EnsembleComplementarityEvidence)->SoloPhraseIntent:
    harmonic_turn.validate(); turn.validate(); complementarity.validate()
    reasons=[]; entry=SoloEntryMode.CONTINUE; target=SoloTargetMode.GUIDE_TONE; density=SoloDensityDirection.STABLE
    families=("passing","neighbor","close_approach"); horizon=2.; register="stable"
    if harmonic_turn.phase is HarmonicTurnPhase.ANTICIPATORY:
        entry=SoloEntryMode.PICKUP; target=SoloTargetMode.NEXT_HARMONY; families=("anticipation","close_approach","passing"); horizon=1.5; reasons.append("future harmony is known")
    elif harmonic_turn.phase is HarmonicTurnPhase.DIRECTED_RESOLUTION:
        target=SoloTargetMode.RESOLUTION; families=("directed_target","resolution_path","close_approach"); reasons.append("current harmony carries resolution pressure")
    elif harmonic_turn.phase is HarmonicTurnPhase.STABLE_FIELD:
        target=SoloTargetMode.COLOR; families=("passing","neighbor","motif_continuation","color_tone"); horizon=3.; reasons.append("stable field permits connective development")
    elif harmonic_turn.phase is HarmonicTurnPhase.FORM_BOUNDARY:
        entry=SoloEntryMode.NEW_PHRASE; target=SoloTargetMode.OPEN; density=SoloDensityDirection.RELEASE; families=("phrase_entry","pickup","guide_tone"); horizon=1.5; reasons.append("form boundary permits phrase reset")
    if turn.episode_type is TurnTakingType.SUPPORTED_HANDOFF_REENTRY:
        entry=SoloEntryMode.CONTINUE
        reasons.append("foreground has already re-entered after supported handoff")
    elif turn.episode_type is TurnTakingType.COLLECTIVE_RELEASE_REENTRY:
        entry=SoloEntryMode.NEW_PHRASE if harmonic_turn.phase is HarmonicTurnPhase.FORM_BOUNDARY else SoloEntryMode.CONTINUE; reasons.append("collective release has already resolved into re-entry")
    elif turn.episode_type is TurnTakingType.FOREGROUND_CONTINUES:
        density=SoloDensityDirection.SPARSE; reasons.append("continued foreground activity favors contrast")
    if complementarity.breath_type is EnsembleBreathType.FOREGROUND_HANDOFF and max(complementarity.low_harmonic_support,complementarity.percussive_support)>=.8:
        density=SoloDensityDirection.SPARSE; reasons.append("active support already carries the handoff")
    elif complementarity.breath_type is EnsembleBreathType.COLLECTIVE_RELEASE and turn.episode_type is not TurnTakingType.COLLECTIVE_RELEASE_REENTRY:
        entry=SoloEntryMode.HOLD_SPACE; density=SoloDensityDirection.RELEASE; target=SoloTargetMode.OPEN; families=("rest","pickup","phrase_entry"); reasons.append("collective release has not yet clearly re-entered")
    shared=SoloMethodContext(
        phrase_maturity=max(0.,min(1.,1.-harmonic_turn.phrase_boundary_pressure)),
        tension=max(0.,min(1.,harmonic_turn.resolution_strength)),
        ensemble_activity=max(0.,min(1.,max(complementarity.low_harmonic_support,complementarity.percussive_support))),
        recent_repetition_count=0,
        phrase_space_available=max(0.,min(1.,complementarity.foreground_drop)),
        form_boundary_pressure=max(0.,min(1.,harmonic_turn.phrase_boundary_pressure)),
        future_harmony_available=harmonic_turn.phase is HarmonicTurnPhase.ANTICIPATORY,
        interaction_role="ANSWER" if turn.episode_type is TurnTakingType.SUPPORTED_HANDOFF_REENTRY else "",
    )
    arc=SoloArc.RELEASE if density is SoloDensityDirection.RELEASE else SoloArc.DEVELOP
    method=max(shared_solo_method_options(shared,arc=arc),key=lambda x:x.weight).operation
    reasons.append(f"shared solo method: {method.value}")
    confidence=max(.25,min(1.,.45*harmonic_turn.confidence+.30*turn.confidence+.25*complementarity.confidence))
    out=SoloPhraseIntent(horizon,entry,target,density,families,method,register,confidence,tuple(reasons)); out.validate(); return out
