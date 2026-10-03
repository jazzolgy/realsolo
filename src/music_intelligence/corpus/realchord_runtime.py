"""Shared RealChord playback/runtime model.

Expands chart-level form into a playback timeline and exposes one session state
that Ensemble, Score/Transcription, AI Player and instrument agents can share.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Sequence

from .realchord import RealChordSong, RealChordMeasure, ExpectedHarmonyReference, expected_harmony_at


@dataclass(frozen=True)
class RealChordPlaybackMeasure:
    playback_measure: int
    source_measure: int
    section: str
    chorus_index: int
    ending: str = ""


@dataclass(frozen=True)
class RealChordPlaybackTimeline:
    realchord_id: str
    measures: tuple[RealChordPlaybackMeasure, ...]
    navigation_status: str = "resolved"
    warnings: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.realchord_id:
            raise ValueError("realchord_id is required")
        for index, item in enumerate(self.measures, start=1):
            if item.playback_measure != index:
                raise ValueError("playback measures must be contiguous and 1-based")
            if item.source_measure < 1:
                raise ValueError("source measure must be 1-based")


@dataclass(frozen=True)
class SharedRealChordSessionState:
    realchord_id: str
    playback_measure: int
    source_measure: int
    beat: float
    section: str = ""
    chorus_index: int = 1
    transpose: int = 0
    tempo: float = 120.0
    style_override: str = ""
    transport: str = "stopped"

    def validate(self) -> None:
        if not self.realchord_id:
            raise ValueError("realchord_id is required")
        if self.playback_measure < 1 or self.source_measure < 1:
            raise ValueError("measure indices are 1-based")
        if self.beat < 0:
            raise ValueError("beat may not be negative")
        if self.chorus_index < 1:
            raise ValueError("chorus_index must be >= 1")
        if self.tempo <= 0:
            raise ValueError("tempo must be positive")
        if self.transport not in {"stopped", "count_in", "playing", "ending"}:
            raise ValueError("unsupported transport state")


def _repeat_pairs(measures: Sequence[RealChordMeasure]) -> tuple[dict[int, int], dict[int, int]]:
    stack: list[int] = []
    starts_to_ends: dict[int, int] = {}
    ends_to_starts: dict[int, int] = {}
    for index, measure in enumerate(measures):
        if measure.repeat_start:
            stack.append(index)
        if measure.repeat_end:
            if stack:
                start = stack.pop()
            else:
                start = 0
                for candidate in range(index, -1, -1):
                    if measures[candidate].section and candidate != index:
                        start = candidate
                        break
            starts_to_ends[start] = index
            ends_to_starts[index] = start
    return starts_to_ends, ends_to_starts


def _expand_explicit_repeats(song: RealChordSong) -> list[int]:
    measures = song.measures
    pairs, reverse = _repeat_pairs(measures)
    repeat_pass: dict[int, int] = {}
    order: list[int] = []
    index = 0
    safety = 0
    safety_limit = max(128, len(measures) * 8)

    while 0 <= index < len(measures) and safety < safety_limit:
        safety += 1
        measure = measures[index]

        active_start: int | None = None
        for start, end in pairs.items():
            if start <= index <= end and (active_start is None or start > active_start):
                active_start = start

        current_pass = repeat_pass.get(active_start, 0) if active_start is not None else 0
        if active_start is not None and current_pass >= 1 and measure.ending == "1":
            repeat_end = pairs.get(active_start, index)
            cursor = index + 1
            while cursor <= repeat_end and measures[cursor].ending in {"", "1"}:
                cursor += 1
            if cursor <= repeat_end and measures[cursor].ending not in {"", "1"}:
                index = cursor
                continue

        order.append(index)

        if index in reverse:
            start = reverse[index]
            if repeat_pass.get(start, 0) == 0:
                repeat_pass[start] = 1
                index = start
                continue
            repeat_pass[start] = 2

        index += 1

    if safety >= safety_limit:
        raise ValueError(f"repeat expansion safety limit hit for {song.realchord_id}")
    return order


def _navigation_indices(song: RealChordSong) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for index, measure in enumerate(song.measures):
        for item in measure.navigation:
            result.setdefault(item, []).append(index)
    return result


def _first_position(order: Sequence[int], source_index: int) -> int | None:
    try:
        return order.index(source_index)
    except ValueError:
        return None


def _apply_navigation(song: RealChordSong, order: list[int]) -> tuple[list[int], str, list[str]]:
    markers = _navigation_indices(song)
    commands: list[tuple[int, str]] = []
    for name in ("dc_al_fine", "dc_al_coda", "dc", "ds_al_fine", "ds_al_coda", "ds"):
        for index in markers.get(name, ()):
            commands.append((index, name))
    if not commands:
        return order, "resolved", []

    command_index, command = sorted(commands)[0]
    command_position = _first_position(order, command_index)
    if command_position is None:
        return order, "partial", ["navigation command was not reached"]

    prefix = order[: command_position + 1]

    if command.startswith("dc"):
        restart_source = 0
    else:
        segnos = markers.get("segno", [])
        if not segnos:
            return order, "partial", ["D.S. command has no Segno marker"]
        restart_source = segnos[0]

    restart_position = _first_position(order, restart_source)
    if restart_position is None:
        return order, "partial", ["navigation restart target missing"]

    replay = order[restart_position:]
    warnings: list[str] = []

    if command.endswith("al_fine"):
        fines = markers.get("fine", [])
        if not fines:
            return prefix + replay, "partial", ["al Fine command has no Fine marker"]
        fine_position = _first_position(replay, fines[0])
        if fine_position is not None:
            replay = replay[: fine_position + 1]
        return prefix + replay, "resolved", warnings

    if command.endswith("al_coda"):
        codas = markers.get("coda", [])
        if not codas:
            return prefix + replay, "partial", ["al Coda command has no Coda marker"]

        to_codas = markers.get("to_coda", [])
        if to_codas:
            cut = _first_position(replay, to_codas[0])
            if cut is not None:
                replay = replay[: cut + 1]

        coda_position = _first_position(order, codas[0])
        if coda_position is None:
            return prefix + replay, "partial", ["Coda target is not in playback order"]
        return prefix + replay + order[coda_position:], "resolved", warnings

    return prefix + replay, "resolved", warnings


def expand_playback_timeline(song: RealChordSong) -> RealChordPlaybackTimeline:
    """Expand repeats and common D.C./D.S./Fine/Coda navigation."""
    song.validate()
    base_order = _expand_explicit_repeats(song)
    order, status, warnings = _apply_navigation(song, base_order)

    playback: list[RealChordPlaybackMeasure] = []
    # One expanded chart traversal is one form pass. Internal repeats/endings do
    # not create a new solo chorus. Chorus count belongs to the session loop.
    chorus_index = 1
    for playback_number, source_index in enumerate(order, start=1):
        source = song.measures[source_index]
        playback.append(RealChordPlaybackMeasure(
            playback_measure=playback_number,
            source_measure=source.measure,
            section=source.section,
            chorus_index=chorus_index,
            ending=source.ending,
        ))

    result = RealChordPlaybackTimeline(
        realchord_id=song.realchord_id,
        measures=tuple(playback),
        navigation_status=status,
        warnings=tuple(warnings),
    )
    result.validate()
    return result


def session_state_at(
    song: RealChordSong,
    timeline: RealChordPlaybackTimeline,
    *,
    playback_measure: int,
    beat: float = 1.0,
    transpose: int = 0,
    tempo: float = 120.0,
    style_override: str = "",
    transport: str = "playing",
    chorus_index: int = 1,
) -> SharedRealChordSessionState:
    timeline.validate()
    if timeline.realchord_id != song.realchord_id:
        raise ValueError("timeline/song realchord_id mismatch")
    try:
        item = timeline.measures[playback_measure - 1]
    except IndexError as exc:
        raise KeyError(playback_measure) from exc

    state = SharedRealChordSessionState(
        realchord_id=song.realchord_id,
        playback_measure=playback_measure,
        source_measure=item.source_measure,
        beat=beat,
        section=item.section,
        chorus_index=chorus_index,
        transpose=transpose,
        tempo=tempo,
        style_override=style_override,
        transport=transport,
    )
    state.validate()
    return state


def expected_harmony_for_state(
    song: RealChordSong,
    state: SharedRealChordSessionState,
) -> ExpectedHarmonyReference | None:
    state.validate()
    if state.realchord_id != song.realchord_id:
        raise ValueError("state/song realchord_id mismatch")
    return expected_harmony_at(song, measure=state.source_measure, beat=state.beat)


def future_harmony(
    song: RealChordSong,
    timeline: RealChordPlaybackTimeline,
    state: SharedRealChordSessionState,
    *,
    lookahead_measures: int = 8,
) -> tuple[tuple[int, int, str, tuple[str, ...]], ...]:
    """Return playback/source/section/chord-symbol tuples for future planning."""
    if lookahead_measures < 0:
        raise ValueError("lookahead_measures may not be negative")
    start = state.playback_measure - 1
    stop = min(len(timeline.measures), start + lookahead_measures + 1)
    rows: list[tuple[int, int, str, tuple[str, ...]]] = []
    for item in timeline.measures[start:stop]:
        measure = song.measure_at(item.source_measure)
        rows.append((
            item.playback_measure,
            item.source_measure,
            item.section,
            tuple(chord.symbol for chord in measure.chords),
        ))
    return tuple(rows)
