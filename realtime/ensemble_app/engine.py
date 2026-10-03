from __future__ import annotations

import time
from typing import Callable

from .beat_tracker import AdaptiveBeatTracker
from .core_bridge import CoreImmediateBridge
from .ensemble_state import EnsembleStateStore
from .models import EnsembleState, MidiObservation, ObservationKind, TransportEvent
from .phrase_tracker import PhraseTracker
from .scheduler import RealtimeScheduler


class EnsembleEngine:
    """Audio/MIDI -> state -> Core immediate choice -> schedule -> listen again."""

    def __init__(
        self,
        core: CoreImmediateBridge,
        sink: Callable[[TransportEvent], None],
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.core = core
        self.clock = clock
        self.beat = AdaptiveBeatTracker()
        self.phrase = PhraseTracker()
        self.ensemble = EnsembleStateStore()
        self.scheduler = RealtimeScheduler(sink, clock=clock)
        self.last_core_latency_s = 0.0

    @property
    def state(self) -> EnsembleState:
        return self.ensemble.state

    def start(self) -> None:
        self.scheduler.start()

    def stop(self) -> None:
        self.scheduler.stop()

    def ingest(self, obs) -> EnsembleState:
        beat = self.beat.update(obs)
        phrase = self.phrase.update(obs, beat)
        state = self.ensemble.update(obs, beat, phrase)

        trigger: str | None = None
        if phrase.phrase_end:
            trigger = "phrase_end"
        elif obs.is_attack:
            trigger = "performer_attack"

        if trigger is not None:
            started = self.clock()
            actions = self.core.decide(state, trigger)
            self.last_core_latency_s = self.clock() - started
            self.scheduler.replace_plan(actions, now=obs.timestamp)
        return state

    def tick(self, now: float | None = None) -> EnsembleState:
        t = self.clock() if now is None else now
        return self.ingest(MidiObservation(t, ObservationKind.CLOCK_TICK))
