from __future__ import annotations

import heapq
import threading
import time
from dataclasses import dataclass, field
from itertools import count
from typing import Callable

from .models import MusicalAction, TransportEvent


@dataclass(order=True)
class _Item:
    when: float
    seq: int
    generation: int | None
    event: TransportEvent = field(compare=False)
    cleanup_after_s: float | None = field(default=None, compare=False)


class RealtimeScheduler:
    """Cancelable future starts + non-cancelable cleanup for committed notes."""

    def __init__(self, sink: Callable[[TransportEvent], None], *, clock: Callable[[], float] = time.monotonic) -> None:
        self.sink = sink
        self.clock = clock
        self._heap: list[_Item] = []
        self._generation = 0
        self._seq = count()
        self._cv = threading.Condition()
        self._running = False
        self._thread: threading.Thread | None = None

    def replace_plan(self, actions: Sequence[MusicalAction], *, now: float | None = None) -> None:
        base = self.clock() if now is None else now
        with self._cv:
            self._generation += 1
            generation = self._generation
            # Preserve mandatory cleanup events (generation=None), cancel only unplayed starts.
            self._heap = [x for x in self._heap if x.generation is None]
            heapq.heapify(self._heap)
            for action in actions:
                event = TransportEvent("note_on", action.pitch_midi, action.velocity, action.channel)
                heapq.heappush(
                    self._heap,
                    _Item(
                        base + max(0.0, action.delay_s),
                        next(self._seq),
                        generation,
                        event,
                        cleanup_after_s=action.duration_s,
                    ),
                )
            self._cv.notify_all()

    def drain_due(self, now: float | None = None) -> list[TransportEvent]:
        now = self.clock() if now is None else now
        emitted: list[TransportEvent] = []
        while True:
            with self._cv:
                if not self._heap or self._heap[0].when > now:
                    break
                item = heapq.heappop(self._heap)
                if item.generation is not None and item.generation != self._generation:
                    continue

            self.sink(item.event)
            emitted.append(item.event)

            if item.event.kind == "note_on" and item.cleanup_after_s is not None:
                off = TransportEvent("note_off", item.event.pitch_midi, 0, item.event.channel)
                with self._cv:
                    # Once note-on was emitted, note-off is mandatory across future re-plans.
                    heapq.heappush(
                        self._heap,
                        _Item(now + max(0.01, item.cleanup_after_s), next(self._seq), None, off),
                    )
                    self._cv.notify_all()
        return emitted

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name="realsolo-midi-scheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        with self._cv:
            self._running = False
            self._cv.notify_all()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run(self) -> None:
        while True:
            with self._cv:
                if not self._running:
                    return
                if not self._heap:
                    self._cv.wait(timeout=0.01)
                    continue
                delay = self._heap[0].when - self.clock()
                if delay > 0:
                    self._cv.wait(timeout=min(delay, 0.01))
                    continue
            self.drain_due()
