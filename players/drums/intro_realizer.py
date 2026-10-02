"""Drum-specific realization policy for shared intro entry decisions."""
from __future__ import annotations
from dataclasses import dataclass
from music_intelligence.reasoning.ensemble_state import InteractionKind, PlayerActionIntent
from music_intelligence.reasoning.intro import EntryAction, EntryDecision

@dataclass(frozen=True)
class DrumIntroPlan:
    action: EntryAction
    intent: PlayerActionIntent
    realization_hint: str
    texture_hint: str="none"

def realize_drum_intro_entry(player_id:str, decision:EntryDecision)->DrumIntroPlan:
    decision.validate(); a=decision.action
    if a is EntryAction.WAIT:
        return DrumIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.HOLD_SPACE,density=0.,energy=.05,space_request=1.),"silence")
    if a is EntryAction.SHADOW:
        return DrumIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.FOLLOW,density=.08,energy=.18,space_request=.9,tags=frozenset({"intro_shadow"})),"breath_texture","brush_or_cymbal_air")
    if a is EntryAction.LIGHT_SUPPORT:
        return DrumIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.SUPPORT,density=.18,energy=.3,space_request=.75,tags=frozenset({"intro_light_support"})),"swell_or_sparse_time","brush_or_cymbal")
    if a is EntryAction.PARTIAL_JOIN:
        return DrumIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.SETUP,density=.4,energy=.5,space_request=.4,tags=frozenset({"intro_partial_join"})),"setup_into_time","ride_or_hat")
    return DrumIntroPlan(a,PlayerActionIntent(player_id,InteractionKind.LOCK,density=.65,energy=.7,space_request=.15,tags=frozenset({"intro_full_join"})),"full_groove_entry","kit")
