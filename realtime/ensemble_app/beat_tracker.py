from __future__ import annotations

from collections import deque
from dataclasses import replace
from statistics import median

from .models import BeatState, MidiObservation


class AdaptiveBeatTracker:
    """MIDI pulse tracker that treats near-simultaneous piano notes as one onset."""

    def __init__(
        self,
        *,
        min_bpm: float = 45.0,
        max_bpm: float = 240.0,
        chord_cluster_s: float = 0.065,
        window: int = 16,
    ) -> None:
        self.min_period = 60.0 / max_bpm
        self.max_period = 60.0 / min_bpm
        self.chord_cluster_s = chord_cluster_s
        self.onsets: deque[float] = deque(maxlen=window)
        self.state = BeatState()

    def update(self, obs: MidiObservation) -> BeatState:
        if obs.is_attack:
            if not self.onsets or obs.timestamp - self.onsets[-1] >= self.chord_cluster_s:
                self.onsets.append(obs.timestamp)
                self._fit_period()
        return self.advance(obs.timestamp)

    def _fit_period(self) -> None:
        if len(self.onsets) < 2:
            if self.onsets:
                self.state = replace(self.state, anchor_time=self.onsets[-1], confidence=0.08)
            return

        intervals = [b - a for a, b in zip(self.onsets, list(self.onsets)[1:]) if b > a]
        target = self.state.beat_period_s
        candidates: list[float] = []
        for dt in intervals[-10:]:
            # Human attacks can be beats, subdivisions or skipped beats.
            hypotheses = (dt, dt * 2.0, dt * 3.0, dt * 4.0, dt / 2.0)
            valid = [x for x in hypotheses if self.min_period <= x <= self.max_period]
            if not valid:
                continue
            if target is None:
                # Prefer a quarter-note pulse near the middle of the practical range.
                reference = 0.5
            else:
                reference = target
            candidates.append(min(valid, key=lambda x: abs(x - reference)))

        if not candidates:
            return

        fitted = median(candidates)
        if target is not None:
            fitted = 0.78 * target + 0.22 * fitted
        spread = median(abs(x - fitted) for x in candidates) if len(candidates) > 1 else fitted * 0.4
        consistency = max(0.0, 1.0 - spread / max(fitted, 1e-6))
        confidence = min(1.0, 0.12 + 0.085 * len(candidates)) * consistency

        self.state = BeatState(
            tempo_bpm=60.0 / fitted,
            beat_period_s=fitted,
            phase=0.0,
            confidence=confidence,
            anchor_time=self.onsets[-1],
        )

    def advance(self, now: float) -> BeatState:
        s = self.state
        if s.anchor_time is None or s.beat_period_s is None:
            return s
        phase = ((now - s.anchor_time) / s.beat_period_s) % 1.0
        self.state = replace(s, phase=phase)
        return self.state
