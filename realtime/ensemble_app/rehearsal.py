from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Sequence

from .stage1_trio import Stage1TrioRuntime


@dataclass(frozen=True, slots=True)
class RehearsalTickLog:
    tick_index: int
    bar_index: int
    beat_in_bar: float
    chord_symbol: str
    next_chord: str
    snapshot_generation: int
    published_generation: int
    directives: tuple[dict, ...]
    intents: tuple[dict, ...]
    gestures: tuple[dict, ...]

    def to_dict(self) -> dict:
        return {
            "tick_index": self.tick_index,
            "bar_index": self.bar_index,
            "beat_in_bar": self.beat_in_bar,
            "chord_symbol": self.chord_symbol,
            "next_chord": self.next_chord,
            "snapshot_generation": self.snapshot_generation,
            "published_generation": self.published_generation,
            "directives": list(self.directives),
            "intents": list(self.intents),
            "gestures": list(self.gestures),
        }


@dataclass(frozen=True, slots=True)
class Stage1RehearsalLog:
    ticks: tuple[RehearsalTickLog, ...]

    def write_jsonl(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            for tick in self.ticks:
                handle.write(json.dumps(tick.to_dict(), ensure_ascii=False, sort_keys=True))
                handle.write("\n")
        return target


def _directive_dict(directive) -> dict:
    return {
        "player_id": directive.player_id,
        "interaction": directive.interaction.value,
        "target_player_ids": list(directive.target_player_ids),
        "density_delta": directive.density_delta,
        "energy_delta": directive.energy_delta,
        "leadership_delta": directive.leadership_delta,
        "space_priority": directive.space_priority,
        "confidence": directive.confidence,
        "reasons": list(directive.reasons),
        "tags": sorted(directive.tags),
    }


def _intent_dict(intent) -> dict:
    return {
        "player_id": intent.player_id,
        "interaction": intent.interaction.value,
        "commitment": intent.commitment.value,
        "density": intent.density,
        "energy": intent.energy,
        "tension": intent.tension,
        "space_request": intent.space_request,
        "leadership": intent.leadership,
        "phrase_maturity": intent.phrase_maturity,
        "target_player_ids": list(intent.target_player_ids),
        "tags": sorted(intent.tags),
        "provenance": list(intent.provenance),
    }


def _tick_log(
    *,
    tick_index: int,
    bar_index: int,
    beat_in_bar: float,
    chord_symbol: str,
    next_chord: str,
    result,
) -> RehearsalTickLog:
    return RehearsalTickLog(
        tick_index=tick_index,
        bar_index=bar_index,
        beat_in_bar=beat_in_bar,
        chord_symbol=chord_symbol,
        next_chord=next_chord,
        snapshot_generation=result.snapshot_generation,
        published_generation=result.state.generation,
        directives=tuple(_directive_dict(x) for x in result.directives),
        intents=tuple(_intent_dict(x.intent) for x in result.decisions),
        gestures=tuple(x.to_dict() for x in result.gestures),
    )


def run_chart_rehearsal(
    runtime: Stage1TrioRuntime,
    chart: Sequence[str],
    *,
    tempo_bpm: float = 120.0,
    beats_per_bar: int = 4,
    section: str = "A",
    chorus: int = 0,
) -> Stage1RehearsalLog:
    """Run a chart one immediate tick at a time and capture causal runtime evidence.

    The helper does not pre-compose future notes. It supplies only current/next
    chart harmony to Stage1TrioRuntime, then records the decisions committed for
    that tick. The next tick therefore sees the state published by the previous
    one.
    """
    if not chart:
        raise ValueError("chart must contain at least one bar")
    if beats_per_bar <= 0:
        raise ValueError("beats_per_bar must be positive")

    ticks: list[RehearsalTickLog] = []
    tick_index = 0
    total_bars = len(chart)

    for bar_index, chord_symbol in enumerate(chart):
        next_chord = chart[(bar_index + 1) % total_bars]
        for beat in range(beats_per_bar):
            result = runtime.decide(
                chord_symbol,
                next_chord,
                beat_in_bar=float(beat),
                bar_index=bar_index,
                total_bars=total_bars,
                tempo_bpm=tempo_bpm,
                section=section,
                chorus=chorus,
            )
            ticks.append(_tick_log(
                tick_index=tick_index,
                bar_index=bar_index,
                beat_in_bar=float(beat),
                chord_symbol=chord_symbol,
                next_chord=next_chord,
                result=result,
            ))
            tick_index += 1

    return Stage1RehearsalLog(tuple(ticks))
