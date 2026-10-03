from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from music_intelligence.reasoning.ensemble_state import (
    CommitmentState,
    EnsembleState,
    InteractionEvent,
    InteractionKind,
    PlayerActionIntent,
    append_interaction,
    update_player_intent,
)
from music_intelligence.reasoning.interaction_scheduler import (
    InteractionDirective,
    schedule_ensemble,
)

from .player_contract import RenderGesture
from .portable_protocol import PortableRenderPacket


@dataclass(frozen=True, slots=True)
class PlayerRuntimeDecision:
    """One player's decision for the current runtime tick.

    The decision contains only immediately committed renderer gestures plus the
    semantic intent that should be published after the shared snapshot has been
    evaluated by every player.
    """

    player_id: str
    intent: PlayerActionIntent
    gestures: tuple[RenderGesture, ...] = ()
    interaction_events: tuple[InteractionEvent, ...] = ()

    def validate(self) -> None:
        if not self.player_id:
            raise ValueError("player_id is required")
        if self.intent.player_id != self.player_id:
            raise ValueError("decision intent must belong to player_id")
        self.intent.validate()
        if self.intent.commitment is CommitmentState.PROVISIONAL:
            raise ValueError("runtime decision must be committed or played")
        for gesture in self.gestures:
            gesture.validate()
        for event in self.interaction_events:
            event.validate()


class EnsemblePlayerProvider(Protocol):
    """Realtime app boundary implemented by instrument player adapters."""

    player_id: str

    def decide_immediate(
        self,
        *,
        snapshot: EnsembleState,
        directive: InteractionDirective,
        context: Mapping[str, object],
    ) -> PlayerRuntimeDecision | None: ...


@dataclass(frozen=True, slots=True)
class RuntimeTickResult:
    snapshot_generation: int
    state: EnsembleState
    directives: tuple[InteractionDirective, ...]
    decisions: tuple[PlayerRuntimeDecision, ...]
    gestures: tuple[RenderGesture, ...]
    skipped_player_ids: tuple[str, ...] = ()

    def to_portable_packets(self, *, sequence_start: int = 0) -> tuple[PortableRenderPacket, ...]:
        """Project committed gestures to the mobile/native runtime boundary."""
        if sequence_start < 0:
            raise ValueError("sequence_start cannot be negative")
        tempo_bpm = float(self.state.transport.tempo_bpm)
        anchor_beat = float(self.state.transport.beat)
        return tuple(
            PortableRenderPacket(
                sequence_id=sequence_start + index,
                generation=self.snapshot_generation,
                tempo_bpm=tempo_bpm,
                anchor_beat=anchor_beat,
                gesture=gesture,
            )
            for index, gesture in enumerate(self.gestures)
        )


class EnsembleRuntimeLoop:
    """Coordinate one causal AI-ensemble decision cycle.

    1. Freeze one shared EnsembleState snapshot.
    2. Compute all InteractionDirectives from that same snapshot.
    3. Ask every registered player for one immediate decision using that
       immutable snapshot.
    4. Only after all providers return, publish committed intents/interactions.
    5. Return renderer gestures.

    This prevents provider ordering from silently changing what later players
    hear during the same tick.
    """

    def __init__(self, providers: Sequence[EnsemblePlayerProvider] = ()) -> None:
        self._providers: dict[str, EnsemblePlayerProvider] = {}
        for provider in providers:
            self.register(provider)

    def register(self, provider: EnsemblePlayerProvider) -> None:
        player_id = provider.player_id
        if not player_id:
            raise ValueError("provider.player_id is required")
        if player_id in self._providers:
            raise ValueError(f"duplicate provider for {player_id}")
        self._providers[player_id] = provider

    def unregister(self, player_id: str) -> None:
        self._providers.pop(player_id, None)

    @property
    def provider_ids(self) -> tuple[str, ...]:
        return tuple(self._providers)

    def step(
        self,
        state: EnsembleState,
        *,
        context: Mapping[str, object] | None = None,
    ) -> RuntimeTickResult:
        state.validate()
        snapshot = state
        shared_context = dict(context or {})
        directives = schedule_ensemble(
            snapshot,
            convention=shared_context.get("performance_convention"),
        )
        by_player = {d.player_id: d for d in directives}

        decisions: list[PlayerRuntimeDecision] = []
        skipped: list[str] = []

        # Every provider reads the same snapshot. Do not mutate state here.
        for presence in snapshot.active_players():
            provider = self._providers.get(presence.player_id)
            if provider is None:
                skipped.append(presence.player_id)
                continue
            directive = by_player[presence.player_id]
            decision = provider.decide_immediate(
                snapshot=snapshot,
                directive=directive,
                context=shared_context,
            )
            if decision is None:
                skipped.append(presence.player_id)
                continue
            decision.validate()
            if decision.player_id != presence.player_id:
                raise ValueError("provider returned decision for another player")
            decisions.append(decision)

        # Atomic publication phase: later providers did not see these updates.
        next_state = snapshot
        gestures: list[RenderGesture] = []
        for decision in decisions:
            next_state = update_player_intent(next_state, decision.intent)
            for event in decision.interaction_events:
                next_state = append_interaction(next_state, event)
            gestures.extend(decision.gestures)

        return RuntimeTickResult(
            snapshot_generation=snapshot.generation,
            state=next_state,
            directives=directives,
            decisions=tuple(decisions),
            gestures=tuple(gestures),
            skipped_player_ids=tuple(skipped),
        )


def committed_intent(
    *,
    player_id: str,
    directive: InteractionDirective,
    density: float,
    energy: float,
    tension: float,
    leadership: float,
    phrase_maturity: float = 0.0,
    tags: frozenset[str] = frozenset(),
    decision_time: float | None = None,
    commit_time: float | None = None,
    provenance: tuple[str, ...] = (),
) -> PlayerActionIntent:
    """Convenience constructor for player adapters.

    Instrument branches remain responsible for deriving these values from their
    actual chosen candidate.
    """
    return PlayerActionIntent(
        player_id=player_id,
        interaction=directive.interaction,
        commitment=CommitmentState.COMMITTED,
        density=density,
        energy=energy,
        tension=tension,
        space_request=directive.space_priority,
        leadership=leadership,
        phrase_maturity=phrase_maturity,
        target_player_ids=directive.target_player_ids,
        tags=frozenset(set(tags) | set(directive.tags)),
        decision_time=decision_time,
        commit_time=commit_time,
        provenance=provenance + ("ensemble_runtime_v146",),
    )
