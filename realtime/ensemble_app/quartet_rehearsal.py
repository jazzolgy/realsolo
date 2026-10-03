from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .chart import SongChart
from .stage1_quartet import Stage1QuartetRuntime


@dataclass(frozen=True, slots=True)
class QuartetRehearsalTick:
    tick_index: int
    bar_index: int
    beat_in_bar: float
    section: str
    chord_symbol: str
    next_chord: str
    snapshot_generation: int
    published_generation: int
    directives: tuple[dict, ...]
    intents: tuple[dict, ...]
    gestures: tuple[dict, ...]
    portable_packets: tuple[dict, ...]

    def to_dict(self) -> dict:
        return {
            "tick_index": self.tick_index,
            "bar_index": self.bar_index,
            "beat_in_bar": self.beat_in_bar,
            "section": self.section,
            "chord_symbol": self.chord_symbol,
            "next_chord": self.next_chord,
            "snapshot_generation": self.snapshot_generation,
            "published_generation": self.published_generation,
            "directives": list(self.directives),
            "intents": list(self.intents),
            "gestures": list(self.gestures),
            "portable_packets": list(self.portable_packets),
        }


@dataclass(frozen=True, slots=True)
class QuartetRehearsalLog:
    title: str
    ticks: tuple[QuartetRehearsalTick, ...]

    def write_jsonl(self, path: str | Path) -> Path:
        target=Path(path)
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("w",encoding="utf-8") as handle:
            for tick in self.ticks:
                handle.write(json.dumps(tick.to_dict(),ensure_ascii=False,sort_keys=True))
                handle.write("\n")
        return target


def _directive_dict(d) -> dict:
    return {
        "player_id": d.player_id,
        "interaction": d.interaction.value,
        "target_player_ids": list(d.target_player_ids),
        "density_delta": d.density_delta,
        "energy_delta": d.energy_delta,
        "leadership_delta": d.leadership_delta,
        "space_priority": d.space_priority,
        "confidence": d.confidence,
        "reasons": list(d.reasons),
        "tags": sorted(d.tags),
    }


def _intent_dict(i) -> dict:
    return {
        "player_id": i.player_id,
        "interaction": i.interaction.value,
        "commitment": i.commitment.value,
        "density": i.density,
        "energy": i.energy,
        "tension": i.tension,
        "space_request": i.space_request,
        "leadership": i.leadership,
        "phrase_maturity": i.phrase_maturity,
        "target_player_ids": list(i.target_player_ids),
        "tags": sorted(i.tags),
        "provenance": list(i.provenance),
    }


def _next_tick_harmony(chart: SongChart, bar_index: int, beat: float, step: float) -> str:
    next_beat=beat+step
    next_bar=bar_index
    if next_beat >= chart.beats_per_bar:
        next_beat=0.0
        next_bar=(bar_index+1)%len(chart.bars)
    return chart.bar(next_bar).chord_at_beat(next_beat,chart.beats_per_bar)


def run_quartet_song_chart(
    runtime: Stage1QuartetRuntime,
    chart: SongChart,
    *,
    subdivisions_per_beat: int = 2,
) -> QuartetRehearsalLog:
    """Run one form through the real four-player immediate-decision path.

    Harmony is sampled at each current tick. Only current + next-tick harmony is
    supplied; no future note sequence is generated.
    """

    if not chart.bars:
        raise ValueError("chart must contain bars")
    if subdivisions_per_beat <= 0:
        raise ValueError("subdivisions_per_beat must be positive")

    ticks=[]
    sequence=0
    step=1.0/subdivisions_per_beat

    for bar_index in range(len(chart.bars)):
        bar=chart.bar(bar_index)
        total_ticks=chart.beats_per_bar*subdivisions_per_beat
        for local_tick in range(total_ticks):
            beat=local_tick*step
            chord=bar.chord_at_beat(beat,chart.beats_per_bar)
            nxt=_next_tick_harmony(chart,bar_index,beat,step)
            result=runtime.decide(
                chord,
                nxt,
                beat_in_bar=beat,
                bar_index=bar_index,
                total_bars=len(chart.bars),
                tempo_bpm=chart.tempo_bpm,
                section=bar.section or "",
                chorus=0,
                song_id=chart.title,
            )
            packets=result.to_portable_packets(sequence_start=sequence)
            sequence += len(packets)

            ticks.append(QuartetRehearsalTick(
                tick_index=len(ticks),
                bar_index=bar_index,
                beat_in_bar=beat,
                section=bar.section or "",
                chord_symbol=chord,
                next_chord=nxt,
                snapshot_generation=result.snapshot_generation,
                published_generation=result.state.generation,
                directives=tuple(_directive_dict(x) for x in result.directives),
                intents=tuple(_intent_dict(x.intent) for x in result.decisions),
                gestures=tuple(x.to_dict() for x in result.gestures),
                portable_packets=tuple(x.to_dict() for x in packets),
            ))

    return QuartetRehearsalLog(chart.title,tuple(ticks))
