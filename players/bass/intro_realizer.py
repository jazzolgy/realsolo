"""Bass-specific realization policy for shared intro entry decisions."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.ensemble_state import InteractionKind, PlayerActionIntent
from music_intelligence.reasoning.intro import EntryAction, EntryDecision

@dataclass(frozen=True)
class BassIntroPlan:
    action: EntryAction
    intent: PlayerActionIntent
    realization_hint: str
    register_hint: str="low"

def realize_bass_intro_entry(player_id:str, decision:EntryDecision)->BassIntroPlan:
    decision.validate(); a=decision.action
    if a is EntryAction.WAIT:
        return BassIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.HOLD_SPACE,density=0.,energy=.1,space_request=1.),"silence")
    if a is EntryAction.SHADOW:
        return BassIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.FOLLOW,density=.12,energy=.2,space_request=.8,tags=frozenset({"intro_shadow"})),"soft_pedal_or_root_hint")
    if a is EntryAction.LIGHT_SUPPORT:
        return BassIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.SUPPORT,density=.2,energy=.3,space_request=.65,tags=frozenset({"intro_light_support"})),"single_root_or_fifth")
    if a is EntryAction.PARTIAL_JOIN:
        return BassIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.LOCK,density=.45,energy=.5,space_request=.35,tags=frozenset({"intro_partial_join"})),"root_plus_approach")
    return BassIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.LOCK,density=.7,energy=.65,space_request=.15,tags=frozenset({"intro_full_join"})),"full_bass_pattern")
