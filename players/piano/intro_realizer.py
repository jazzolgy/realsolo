"""Piano-specific realization policy for shared intro entry decisions."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.ensemble_state import InteractionKind, PlayerActionIntent
from music_intelligence.reasoning.intro import EntryAction, EntryDecision

@dataclass(frozen=True)
class PianoIntroPlan:
    action: EntryAction
    intent: PlayerActionIntent
    realization_hint: str
    register_hint: str="mid"
    pedal_hint: str="none"

def realize_piano_intro_entry(player_id:str, decision:EntryDecision)->PianoIntroPlan:
    decision.validate()
    action=decision.action
    if action is EntryAction.WAIT:
        return PianoIntroPlan(action,PlayerActionIntent(player_id,InteractionKind.HOLD_SPACE,density=0.,energy=.1,space_request=1.,leadership=0.),"silence")
    if action is EntryAction.SHADOW:
        return PianoIntroPlan(action,PlayerActionIntent(player_id,InteractionKind.FOLLOW,density=.15,energy=.2,space_request=.75,leadership=.05,tags=frozenset({"intro_shadow"})),"single_tone_or_soft_shell","mid_high","none")
    if action is EntryAction.LIGHT_SUPPORT:
        return PianoIntroPlan(action,PlayerActionIntent(player_id,InteractionKind.SUPPORT,density=.25,energy=.3,space_request=.6,leadership=.05,tags=frozenset({"intro_light_support"})),"sparse_shell_voicing","mid","half")
    if action is EntryAction.PARTIAL_JOIN:
        return PianoIntroPlan(action,PlayerActionIntent(player_id,InteractionKind.FOLLOW,density=.45,energy=.5,space_request=.35,leadership=.1,tags=frozenset({"intro_partial_join"})),"rhythmic_comping_entry","mid","none")
    return PianoIntroPlan(action,PlayerActionIntent(player_id,InteractionKind.LOCK,density=.65,energy=.65,space_request=.15,leadership=.1,tags=frozenset({"intro_full_join"})),"full_comping_entry","mid","none")
