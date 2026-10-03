from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ChartBar:
    chords: tuple[str, ...]
    section: str | None = None
    rehearsal_mark: str | None = None

    def chord_at_beat(self, beat_in_bar: float, beats_per_bar: int) -> str:
        if not self.chords:
            return ""
        slot = min(len(self.chords) - 1, int((beat_in_bar / max(1, beats_per_bar)) * len(self.chords)))
        return self.chords[slot]


@dataclass(frozen=True, slots=True)
class SongChart:
    title: str
    bars: tuple[ChartBar, ...]
    tempo_bpm: float = 120.0
    beats_per_bar: int = 4
    beat_unit: int = 4
    choruses: int = 1

    @property
    def total_bars(self) -> int:
        return len(self.bars) * max(1, self.choruses)

    @property
    def beat_period_s(self) -> float:
        return 60.0 / self.tempo_bpm

    def bar(self, absolute_bar: int) -> ChartBar:
        if not self.bars:
            raise IndexError("chart has no bars")
        return self.bars[absolute_bar % len(self.bars)]

    @classmethod
    def from_progression(
        cls,
        title: str,
        progression: Iterable[str],
        *,
        tempo_bpm: float = 120.0,
        beats_per_bar: int = 4,
        choruses: int = 1,
    ) -> "SongChart":
        return cls(
            title=title,
            bars=tuple(ChartBar(tuple(ch.strip() for ch in bar.split("|") if ch.strip())) for bar in progression),
            tempo_bpm=tempo_bpm,
            beats_per_bar=beats_per_bar,
            choruses=choruses,
        )
