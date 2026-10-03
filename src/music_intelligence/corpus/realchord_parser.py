"""Structural RealChord parser built on the existing raw-ingestion contract.

Raw playlist ingestion owns stable repertoire identity (source-order
realchord_id). This module decodes the chart payload and normalizes musical
structure for Expected Harmony / form use by every app and AI player.
"""
from __future__ import annotations

import re
from typing import Mapping

from .realchord_ingestion import RealChordRawSong, parse_realchord_playlist_html


_MAGIC = "1r34LbKcu7"
_SECTION_RE = re.compile(r"\*([A-DVi])")
_TIMESIG_RE = re.compile(r"T(\d)(\d)")
_ENDING_RE = re.compile(r"N(\d+)")
_STAFF_RE = re.compile(r"<([^>]*)>")


def _hussle(value: str) -> str:
    text = value
    result = ""
    while len(text) > 50:
        segment = text[:50]
        text = text[50:]
        if len(text) < 2:
            result += segment
            continue
        result += (
            segment[45:50][::-1]
            + segment[5:10]
            + segment[26:40][::-1]
            + segment[24:26]
            + segment[10:24][::-1]
            + segment[40:45]
            + segment[0:5][::-1]
        )
    return result + text


def decode_progression(payload: str) -> str:
    """Decode the modern chart payload into the plain 16-cell grid string."""
    text = payload[len(_MAGIC):] if payload.startswith(_MAGIC) else payload
    text = _hussle(text)
    return text.replace("XyQ", "   ").replace("LZ", " |").replace("Kcl", "| x")


def _strip_controls(raw: str) -> str:
    text = _STAFF_RE.sub("", raw)
    text = _SECTION_RE.sub("", text)
    text = _TIMESIG_RE.sub("", text)
    text = _ENDING_RE.sub("", text)
    for token in ("Q", "S", "Y", "U"):
        text = text.replace(token, "")
    return text.strip()


def _split_measures(progression: str) -> list[tuple[str, str, str | None]]:
    bars: list[tuple[str, str, str | None]] = []
    buffer = ""
    open_bar = ""

    for char in progression:
        if char in "[{":
            if _strip_controls(buffer):
                bars.append((open_bar, buffer, None))
                buffer = ""
            open_bar = char
        elif char == "|":
            if _strip_controls(buffer):
                bars.append((open_bar, buffer, "|"))
                buffer = ""
                open_bar = "|"
            else:
                open_bar = "|"
        elif char in "]}Z":
            if _strip_controls(buffer) or buffer.strip() or open_bar:
                bars.append((open_bar, buffer, char))
                buffer = ""
                open_bar = ""
        else:
            buffer += char

    if _strip_controls(buffer) or buffer.strip() or open_bar:
        bars.append((open_bar, buffer, None))
    return bars


def _content_cells(raw: str) -> tuple[list[str | None], str]:
    text = _STAFF_RE.sub("", raw)
    text = _SECTION_RE.sub("", text)
    text = _TIMESIG_RE.sub("", text)
    text = _ENDING_RE.sub("", text)
    for token in ("Q", "S", "Y", "U"):
        text = text.replace(token, "")

    text = re.sub(r"(?<![A-Za-z])s(?=[A-Gnrx(])", "", text)
    text = re.sub(r"(?<=[A-G0-9)])l(?=\s|$)", "", text)

    if "," in text:
        return [part.strip() or None for part in text.split(",")], "comma"

    cells: list[str | None] = []
    index = 0
    while index < len(text):
        if text[index] == " ":
            cells.append(None)
            index += 1
            continue
        if text[index] in "\t\r\n":
            index += 1
            continue
        end = index
        while end < len(text) and text[end] not in " \t\r\n":
            end += 1
        cells.append(text[index:end])
        index = end

    while len(cells) > 4 and all(item is None for item in cells[:4]):
        cells = cells[4:]
    return cells, "grid"


def _is_chord(token: str | None) -> bool:
    if not token or token in {"x", "r", "n", "p"}:
        return False
    return bool(re.match(r"^\(?[A-G](?:b|#)?", token))


def _chord_symbol(token: str) -> str:
    match = re.match(r"^([^()]+)(?:\(([^()]+)\))?$", token)
    return match.group(1) if match else token


def _navigation(raw: str) -> tuple[str, ...]:
    out: list[str] = []
    staff = " ".join(_STAFF_RE.findall(raw)).lower()
    if "S" in raw:
        out.append("segno")
    if "Q" in raw:
        out.append("coda")
    if "fine" in staff:
        out.append("fine")
    if "to coda" in staff:
        out.append("to_coda")
    if "d.c" in staff:
        out.append("dc_al_coda" if "coda" in staff else "dc_al_fine" if "fine" in staff else "dc")
    if "d.s" in staff:
        out.append("ds_al_coda" if "coda" in staff else "ds_al_fine" if "fine" in staff else "ds")
    return tuple(dict.fromkeys(out))


def parse_progression(progression: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Normalize one decoded progression into measures/chords/navigation."""
    bars = _split_measures(progression)
    measures: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    current_section = ""
    current_time_signature = "4/4"
    previous_chords: list[dict[str, object]] | None = None
    two_back_chords: list[dict[str, object]] | None = None

    for number, (open_bar, raw, close_bar) in enumerate(bars, start=1):
        section = _SECTION_RE.search(raw)
        if section:
            current_section = section.group(1)

        time_sig = _TIMESIG_RE.search(raw)
        if time_sig:
            current_time_signature = f"{time_sig.group(1)}/{time_sig.group(2)}"

        ending_match = _ENDING_RE.search(raw)
        cells, layout = _content_cells(raw)
        meaningful = [item for item in cells if item]

        repeat_previous = len(meaningful) == 1 and meaningful[0] == "x"
        repeat_two = len(meaningful) == 1 and meaningful[0] == "r"
        no_chord = len(meaningful) == 1 and meaningful[0] == "n"

        if repeat_previous and previous_chords is not None:
            chords = [dict(item) for item in previous_chords]
        elif repeat_two and two_back_chords is not None:
            chords = [dict(item) for item in two_back_chords]
        elif no_chord:
            chords = []
        else:
            chord_cells = [(i, token) for i, token in enumerate(cells) if _is_chord(token)]
            chords: list[dict[str, object]] = []
            try:
                beats_in_bar = float(current_time_signature.split("/")[0])
            except ValueError:
                beats_in_bar = 4.0

            if layout == "grid" and len(cells) == 4 and chord_cells:
                for pos, (cell_index, token) in enumerate(chord_cells):
                    next_index = chord_cells[pos + 1][0] if pos + 1 < len(chord_cells) else 4
                    start_fraction = cell_index / 4.0
                    duration_fraction = (next_index - cell_index) / 4.0
                    chords.append({
                        "beat": 1.0 + start_fraction * beats_in_bar,
                        "symbol": _chord_symbol(str(token)),
                        "confidence": 0.95,
                        "duration_beats": duration_fraction * beats_in_bar,
                    })
            else:
                tokens = [str(token) for _, token in chord_cells]
                count = len(tokens)
                for index, token in enumerate(tokens):
                    chords.append({
                        "beat": 1.0 + (index / max(count, 1)) * beats_in_bar,
                        "symbol": _chord_symbol(token),
                        "confidence": 0.70,
                        "duration_beats": beats_in_bar / max(count, 1),
                    })

        if len(cells) not in {0, 4} and not (repeat_previous or repeat_two or no_chord):
            warnings.append({
                "measure": number,
                "type": "nonstandard_cell_layout",
                "cell_count": len(cells),
            })

        nav = list(_navigation(raw))
        if repeat_previous:
            nav.append("repeat_previous_measure")
        if repeat_two:
            nav.append("repeat_previous_two_measures")
        if no_chord:
            nav.append("no_chord")

        measures.append({
            "measure": number,
            "section": current_section,
            "time_signature": current_time_signature,
            "chords": chords,
            "repeat_start": open_bar == "{",
            "repeat_end": close_bar == "}",
            "ending": ending_match.group(1) if ending_match else "",
            "navigation": nav,
        })
        two_back_chords = previous_chords
        previous_chords = chords

    return measures, warnings


def normalize_raw_song(raw: RealChordRawSong) -> dict[str, object]:
    """Decode one existing raw-ingestion item without changing realchord_id."""
    progression = decode_progression(raw.raw_chart)
    measures, warnings = parse_progression(progression)
    return {
        "realchord_id": raw.realchord_id,
        "title": raw.title,
        "composer": raw.composer,
        "style": raw.style,
        "key": raw.key,
        "measures": measures,
        "parser_warnings": warnings,
    }


def normalize_playlist_html(text: str) -> dict[str, object]:
    """Return the full normalized corpus using existing stable RealChord ids."""
    raw_songs = parse_realchord_playlist_html(text)
    songs = [normalize_raw_song(raw) for raw in raw_songs]
    return {
        "schema": "RealChordNormalizedCorpus",
        "schema_version": "1.0",
        "song_count": len(songs),
        "songs": songs,
    }
