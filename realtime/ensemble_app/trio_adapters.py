from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Protocol

from music_intelligence.reasoning.ensemble_state import (
    InteractionEvent,
    InteractionKind,
)
from music_intelligence.reasoning.interaction_scheduler import InteractionDirective

from .player_contract import RenderGesture, apply_shared_groove_to_render_gesture
from .runtime_loop import (
    PlayerRuntimeDecision,
    committed_intent,
)


@dataclass(frozen=True, slots=True)
class NativeImmediateResult:
    """Normalized immediate output expected from an instrument branch.

    Instrument branches remain free to use their own candidate/state classes
    internally.  At the realtime boundary they expose one committed gesture plus
    coordination-relevant scalars.
    """

    gesture: RenderGesture | None
    density: float
    energy: float
    tension: float
    leadership: float = 0.0
    phrase_maturity: float = 0.0
    tags: frozenset[str] = frozenset()
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.gesture is not None:
            self.gesture.validate()
        for value, name in (
            (self.density, "density"),
            (self.energy, "energy"),
            (self.tension, "tension"),
            (self.leadership, "leadership"),
            (self.phrase_maturity, "phrase_maturity"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


class NativeImmediateDecider(Protocol):
    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None: ...


class _BaseRuntimeAdapter:
    player_id: str
    role_name: str

    def __init__(
        self,
        decider: NativeImmediateDecider | None = None,
        *,
        source: str,
    ) -> None:
        self._decider = decider
        self.source = source

    @property
    def available(self) -> bool:
        return self._decider is not None

    def _native_context(
        self,
        *,
        snapshot,
        directive: InteractionDirective,
        context: Mapping[str, object],
    ) -> dict[str, object]:
        return {
            **dict(context),
            "player_id": self.player_id,
            "role": self.role_name,
            "ensemble_snapshot": snapshot,
            "interaction_directive": directive,
            "interaction_kind": directive.interaction.value,
            "target_player_ids": directive.target_player_ids,
            "density_delta": directive.density_delta,
            "energy_delta": directive.energy_delta,
            "leadership_delta": directive.leadership_delta,
            "space_priority": directive.space_priority,
            "directive_confidence": directive.confidence,
            "directive_tags": directive.tags,
        }

    def decide_immediate(self, *, snapshot, directive, context):
        if self._decider is None:
            return None

        native = self._decider(self._native_context(
            snapshot=snapshot,
            directive=directive,
            context=context,
        ))
        if native is None:
            return None
        if native.gesture is not None:
            native = NativeImmediateResult(
                gesture=apply_shared_groove_to_render_gesture(
                    native.gesture,
                    anchor_beat=snapshot.transport.beat,
                    groove=snapshot.groove,
                    phrase_maturity=native.phrase_maturity,
                ),
                density=native.density,
                energy=native.energy,
                tension=native.tension,
                leadership=native.leadership,
                phrase_maturity=native.phrase_maturity,
                tags=frozenset(
                    set(native.tags)
                    | ({f"groove:{snapshot.groove.feel.value}"} if snapshot.groove is not None else set())
                ),
                provenance=native.provenance + (("shared_groove_projection",) if snapshot.groove is not None else ()),
            )
        native.validate()

        density = max(0.0, min(1.0, native.density + directive.density_delta))
        energy = max(0.0, min(1.0, native.energy + directive.energy_delta))
        leadership = max(
            0.0,
            min(1.0, native.leadership + directive.leadership_delta),
        )

        intent = committed_intent(
            player_id=self.player_id,
            directive=directive,
            density=density,
            energy=energy,
            tension=native.tension,
            leadership=leadership,
            phrase_maturity=native.phrase_maturity,
            tags=native.tags,
            provenance=native.provenance + (self.source,),
        )

        gestures = (native.gesture,) if native.gesture is not None else ()
        event = InteractionEvent(
            source_player_id=self.player_id,
            kind=directive.interaction,
            target_player_ids=directive.target_player_ids,
            tags=frozenset(set(native.tags) | set(directive.tags)),
            confidence=directive.confidence,
        )
        return PlayerRuntimeDecision(
            player_id=self.player_id,
            intent=intent,
            gestures=gestures,
            interaction_events=(event,),
        )


class PianoRuntimeAdapter(_BaseRuntimeAdapter):
    player_id = "piano"
    role_name = "comping"

    def __init__(self, decider: NativeImmediateDecider | None = None) -> None:
        super().__init__(decider, source="adapter:player/piano")


class BassRuntimeAdapter(_BaseRuntimeAdapter):
    player_id = "bass"
    role_name = "bass"

    def __init__(self, decider: NativeImmediateDecider | None = None) -> None:
        super().__init__(decider, source="adapter:player/bass")


class DrumsRuntimeAdapter(_BaseRuntimeAdapter):
    player_id = "drums"
    role_name = "drums"

    def __init__(self, decider: NativeImmediateDecider | None = None) -> None:
        super().__init__(decider, source="adapter:player/drums")


@dataclass(frozen=True, slots=True)
class TrioAdapterStatus:
    player_id: str
    adapter_ready: bool
    native_decider_connected: bool
    source: str


def trio_adapter_status(
    piano: PianoRuntimeAdapter,
    bass: BassRuntimeAdapter,
    drums: DrumsRuntimeAdapter,
) -> tuple[TrioAdapterStatus, ...]:
    return (
        TrioAdapterStatus("piano", True, piano.available, piano.source),
        TrioAdapterStatus("bass", True, bass.available, bass.source),
        TrioAdapterStatus("drums", True, drums.available, drums.source),
    )
