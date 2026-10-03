from __future__ import annotations

from dataclasses import dataclass

from .chart import SongChart


@dataclass(frozen=True, slots=True)
class ChartPosition:
    absolute_bar: int
    bar_in_form: int
    chorus_index: int
    beat_in_bar: float
    chord_symbol: str
    section: str | None
    finished: bool = False


class ChartTransport:
    """Deterministic Stage-1 musical clock.

    Interactive audio-following may later bend this expectation, but Stage 1
    remains fully usable without a microphone.
    """

    def __init__(self, chart: SongChart) -> None:
        self.chart = chart
        self._started_at: float | None = None
        self._paused_at: float | None = None
        self._pause_accumulated = 0.0

    def start(self, now: float) -> None:
        self._started_at = now
        self._paused_at = None
        self._pause_accumulated = 0.0

    def pause(self, now: float) -> None:
        if self._started_at is not None and self._paused_at is None:
            self._paused_at = now

    def resume(self, now: float) -> None:
        if self._paused_at is not None:
            self._pause_accumulated += now - self._paused_at
            self._paused_at = None

    def position(self, now: float) -> ChartPosition:
        if self._started_at is None:
            elapsed = 0.0
        else:
            effective_now = self._paused_at if self._paused_at is not None else now
            elapsed = max(0.0, effective_now - self._started_at - self._pause_accumulated)

        beat = elapsed / self.chart.beat_period_s
        absolute_bar = int(beat // self.chart.beats_per_bar)
        finished = absolute_bar >= self.chart.total_bars
        if finished:
            absolute_bar = max(0, self.chart.total_bars - 1)
            beat_in_bar = float(self.chart.beats_per_bar)
        else:
            beat_in_bar = beat % self.chart.beats_per_bar

        form_len = max(1, len(self.chart.bars))
        chorus_index = absolute_bar // form_len
        bar_in_form = absolute_bar % form_len
        bar = self.chart.bar(absolute_bar)
        return ChartPosition(
            absolute_bar=absolute_bar,
            bar_in_form=bar_in_form,
            chorus_index=chorus_index,
            beat_in_bar=beat_in_bar,
            chord_symbol=bar.chord_at_beat(beat_in_bar, self.chart.beats_per_bar),
            section=bar.section,
            finished=finished,
        )
