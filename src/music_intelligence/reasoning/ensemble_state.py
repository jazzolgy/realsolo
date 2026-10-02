"""v1.43 shared ensemble state and player-action intent contract.

This module defines the common live state that all AI players may read and the
small, instrument-neutral messages they may publish about their current
intention / committed action.

It is deliberately not a centralized composer. Each player retains its own
instrument grammar and candidate generation. The shared state exists so players
can listen to one another, coordinate density/leadership/space, and react after
each immediate commitment.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Mapping, Sequence

from .groove_context import GrooveTemporalContext


class PlayerRole(str, Enum):
    SOLOIST = "soloist"
    COMPER = "comper"
    BASS = "bass"
    DRUMS = "drums"
    MELODY = "melody"
    SUPPORT = "support"
    LEADER = "leader"
    FOLLOWER = "follower"
    UNKNOWN = "unknown"


class InteractionKind(str, Enum):
    LEAD = "lead"
    FOLLOW = "follow"
    ANSWER = "answer"
    SUPPORT = "support"
    YIELD = "yield"
    BUILD = "build"
    PUNCTUATE = "punctuate"
    SETUP = "setup"
    LOCK = "lock"
    CONTRAST = "contrast"
    HOLD_SPACE = "hold_space"
    TRANSITION = "transition"
    NONE = "none"


class CommitmentState(str, Enum):
    PROVISIONAL = "provisional"
    COMMITTED = "committed"
    PLAYED = "played"


@dataclass(frozen=True)
class TransportState:
    beat: float
    bar: int
    section: str = ""
    chorus: int = 0
    tempo_bpm: float = 120.0
    meter_numerator: int = 4
    meter_denominator: int = 4
    form_position: float = 0.0

    def validate(self) -> None:
        if self.bar < 0 or self.chorus < 0:
            raise ValueError("bar / chorus may not be negative")
        if self.tempo_bpm <= 0:
            raise ValueError("tempo_bpm must be positive")
        if self.meter_numerator <= 0 or self.meter_denominator <= 0:
            raise ValueError("meter values must be positive")
        if not 0.0 <= self.form_position <= 1.0:
            raise ValueError("form_position must be within 0..1")


@dataclass(frozen=True)
class PlayerPresence:
    player_id: str
    instrument: str
    role: PlayerRole = PlayerRole.UNKNOWN
    active: bool = True

    def validate(self) -> None:
        if not self.player_id:
            raise ValueError("player_id is required")
        if not self.instrument:
            raise ValueError("instrument is required")


@dataclass(frozen=True)
class PlayerActionIntent:
    """Short-lived message about a player's current musical intention.

    This is not a future score. Exact note payloads live in instrument-specific
    committed events. Shared state carries only coordination-relevant semantics.
    """

    player_id: str
    interaction: InteractionKind
    commitment: CommitmentState = CommitmentState.PROVISIONAL
    density: float = 0.5
    energy: float = 0.5
    tension: float = 0.5
    space_request: float = 0.0
    leadership: float = 0.0
    phrase_maturity: float = 0.0
    target_player_ids: tuple[str, ...] = ()
    tags: frozenset[str] = frozenset()
    decision_time: float | None = None
    commit_time: float | None = None
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.player_id:
            raise ValueError("player_id is required")
        for value, name in (
            (self.density, "density"),
            (self.energy, "energy"),
            (self.tension, "tension"),
            (self.space_request, "space_request"),
            (self.leadership, "leadership"),
            (self.phrase_maturity, "phrase_maturity"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if (
            self.decision_time is not None
            and self.commit_time is not None
            and self.commit_time < self.decision_time
        ):
            raise ValueError("commit_time may not precede decision_time")


@dataclass(frozen=True)
class InteractionEvent:
    source_player_id: str
    kind: InteractionKind
    target_player_ids: tuple[str, ...] = ()
    beat: float | None = None
    tags: frozenset[str] = frozenset()
    confidence: float = 1.0

    def validate(self) -> None:
        if not self.source_player_id:
            raise ValueError("source_player_id is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class EnsembleState:
    transport: TransportState
    players: tuple[PlayerPresence, ...] = ()
    intents: tuple[PlayerActionIntent, ...] = ()
    recent_interactions: tuple[InteractionEvent, ...] = ()
    harmonic_state_id: str | None = None
    ensemble_density: float = 0.5
    ensemble_energy: float = 0.5
    ensemble_tension: float = 0.5
    space_available: float = 0.5
    leader_player_id: str | None = None
    groove: GrooveTemporalContext | None = None
    generation: int = 0

    def validate(self) -> None:
        self.transport.validate()
        for p in self.players:
            p.validate()
        for i in self.intents:
            i.validate()
        for event in self.recent_interactions:
            event.validate()
        if self.groove is not None:
            self.groove.validate()
        ids = [p.player_id for p in self.players]
        if len(ids) != len(set(ids)):
            raise ValueError("player_id values must be unique")
        for value, name in (
            (self.ensemble_density, "ensemble_density"),
            (self.ensemble_energy, "ensemble_energy"),
            (self.ensemble_tension, "ensemble_tension"),
            (self.space_available, "space_available"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.generation < 0:
            raise ValueError("generation may not be negative")

    def intent_for(self, player_id: str) -> PlayerActionIntent | None:
        for intent in reversed(self.intents):
            if intent.player_id == player_id:
                return intent
        return None

    def active_players(self) -> tuple[PlayerPresence, ...]:
        return tuple(x for x in self.players if x.active)


@dataclass(frozen=True)
class PlayerEnsembleView:
    self_player_id: str
    other_intents: tuple[PlayerActionIntent, ...]
    recent_interactions: tuple[InteractionEvent, ...]
    ensemble_density: float
    ensemble_energy: float
    ensemble_tension: float
    space_available: float
    leader_player_id: str | None
    groove: GrooveTemporalContext | None


def player_view(state: EnsembleState, player_id: str) -> PlayerEnsembleView:
    state.validate()
    known = {p.player_id for p in state.players}
    if player_id not in known:
        raise ValueError(f"unknown player_id: {player_id}")
    return PlayerEnsembleView(
        self_player_id=player_id,
        other_intents=tuple(i for i in state.intents if i.player_id != player_id),
        recent_interactions=state.recent_interactions,
        ensemble_density=state.ensemble_density,
        ensemble_energy=state.ensemble_energy,
        ensemble_tension=state.ensemble_tension,
        space_available=state.space_available,
        leader_player_id=state.leader_player_id,
        groove=state.groove,
    )


def _aggregate_intents(
    intents: Sequence[PlayerActionIntent],
) -> tuple[float, float, float, float, str | None]:
    if not intents:
        return .0, .0, .0, 1.0, None

    density = sum(x.density for x in intents) / len(intents)
    energy = sum(x.energy for x in intents) / len(intents)
    tension = sum(x.tension for x in intents) / len(intents)

    # Explicit space requests and total density both affect room available.
    requested_space = max((x.space_request for x in intents), default=0.0)
    space = max(0.0, min(1.0, 1.0 - .65 * density - .35 * requested_space))

    leader = max(intents, key=lambda x: x.leadership)
    leader_id = leader.player_id if leader.leadership >= .55 else None
    return density, energy, tension, space, leader_id


def update_player_intent(
    state: EnsembleState,
    intent: PlayerActionIntent,
    *,
    max_intents_per_player: int = 2,
) -> EnsembleState:
    state.validate()
    intent.validate()
    if intent.player_id not in {p.player_id for p in state.players}:
        raise ValueError("intent references unknown player")

    retained: list[PlayerActionIntent] = []
    same_player: list[PlayerActionIntent] = []
    for old in state.intents:
        if old.player_id == intent.player_id:
            same_player.append(old)
        else:
            retained.append(old)

    same_player = same_player[-max(0, max_intents_per_player - 1):]
    intents = tuple(retained + same_player + [intent])
    density, energy, tension, space, leader = _aggregate_intents(intents)

    return EnsembleState(
        transport=state.transport,
        players=state.players,
        intents=intents,
        recent_interactions=state.recent_interactions,
        harmonic_state_id=state.harmonic_state_id,
        ensemble_density=density,
        ensemble_energy=energy,
        ensemble_tension=tension,
        space_available=space,
        leader_player_id=leader,
        groove=state.groove,
        generation=state.generation + 1,
    )


def append_interaction(
    state: EnsembleState,
    event: InteractionEvent,
    *,
    history_limit: int = 32,
) -> EnsembleState:
    state.validate()
    event.validate()
    history = (state.recent_interactions + (event,))[-history_limit:]
    return replace(
        state,
        recent_interactions=history,
        generation=state.generation + 1,
    )


def advance_transport(state: EnsembleState, transport: TransportState) -> EnsembleState:
    state.validate()
    transport.validate()
    return replace(state, transport=transport, generation=state.generation + 1)
