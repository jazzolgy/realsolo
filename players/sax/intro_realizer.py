"""Sax-specific realization policy for shared intro entry decisions."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.ensemble_state import InteractionKind, PlayerActionIntent
from music_intelligence.reasoning.intro import EntryAction, EntryDecision

@dataclass(frozen=True)
class SaxIntroPlan:
    action: EntryAction
    intent: PlayerActionIntent
    realization_hint: str

def realize_sax_intro_entry(player_id:str, decision:EntryDecision, *, is_head_leader:bool=False)->SaxIntroPlan:
    decision.validate(); a=decision.action
    if is_head_leader and a in {EntryAction.PARTIAL_JOIN,EntryAction.FULL_JOIN}:
        return SaxIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.LEAD,density=.6,energy=.65,leadership=.9,tags=frozenset({"intro_head_leader"})),"continue_head_or_pickup")
    if a is EntryAction.WAIT:
        return SaxIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.HOLD_SPACE,density=0.,energy=.1,space_request=1.),"silence")
    if a is EntryAction.SHADOW:
        return SaxIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.FOLLOW,density=.08,energy=.2,space_request=.9,tags=frozenset({"intro_shadow"})),"breath_or_very_soft_echo")
    if a is EntryAction.LIGHT_SUPPORT:
        return SaxIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.ANSWER,density=.15,energy=.3,space_request=.75,tags=frozenset({"intro_light_support"})),"short_response")
    if a is EntryAction.PARTIAL_JOIN:
        return SaxIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.FOLLOW,density=.35,energy=.5,space_request=.45,tags=frozenset({"intro_partial_join"})),"pickup_or_head_fragment")
    return SaxIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.LOCK,density=.55,energy=.65,space_request=.25,tags=frozenset({"intro_full_join"})),"full_head_entry")
