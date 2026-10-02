"""Instrument-specific adapter from Shared EnsembleState to Bass cues.

Shared Core owns EnsembleState and PlayerActionIntent. Bass only derives the
small set of cues its canonical policy needs; it does not mutate or reinterpret
shared form/harmony.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    InteractionKind,
    PlayerRole,
)


@dataclass(frozen=True)
class BassEnsembleSignals:
    ensemble_activity: float = .5
    phrase_progress: float | None = None
    soloist_phrase_ending: bool = False
    drum_fill_active: bool = False
    piano_fill_active: bool = False
    low_register_conflict: bool = False
    provenance: tuple[str, ...] = ()


def derive_bass_ensemble_signals(
    state: EnsembleState,
    *,
    bass_player_id: str,
) -> BassEnsembleSignals:
    """Derive bass-local cues from one immutable Shared EnsembleState."""
    state.validate()
    players = {p.player_id: p for p in state.players}
    if bass_player_id not in players:
        raise ValueError("unknown bass_player_id")

    latest = {}
    for intent in state.intents:
        latest[intent.player_id] = intent

    foreground = []
    for player_id, intent in latest.items():
        if player_id == bass_player_id:
            continue
        presence = players.get(player_id)
        if presence is None or not presence.active:
            continue
        if presence.role in {
            PlayerRole.SOLOIST,
            PlayerRole.LEADER,
            PlayerRole.MELODY,
        } or intent.leadership >= .55:
            foreground.append(intent)

    leader = None
    if foreground:
        leader = max(
            foreground,
            key=lambda x: (x.leadership, x.phrase_maturity, x.energy),
        )

    phrase_progress = leader.phrase_maturity if leader is not None else None
    ending = bool(leader is not None and leader.phrase_maturity >= .72)

    drum_fill = False
    piano_fill = False
    for player_id, intent in latest.items():
        if player_id == bass_player_id:
            continue
        presence = players.get(player_id)
        if presence is None:
            continue
        active_fill = intent.interaction in {
            InteractionKind.ANSWER,
            InteractionKind.PUNCTUATE,
            InteractionKind.SETUP,
            InteractionKind.TRANSITION,
        } and intent.density >= .52
        instrument = presence.instrument.lower()
        if active_fill and "drum" in instrument:
            drum_fill = True
        if active_fill and ("piano" in instrument or presence.role is PlayerRole.COMPER):
            piano_fill = True

    # Activity is intentionally mostly density, with energy providing a smaller
    # correction so loud/sparse and dense/soft textures remain distinguishable.
    activity = max(
        0.0,
        min(1.0, .72 * state.ensemble_density + .28 * state.ensemble_energy),
    )

    return BassEnsembleSignals(
        ensemble_activity=activity,
        phrase_progress=phrase_progress,
        soloist_phrase_ending=ending,
        drum_fill_active=drum_fill,
        piano_fill_active=piano_fill,
        low_register_conflict=False,
        provenance=("shared_ensemble_state", f"generation:{state.generation}"),
    )
