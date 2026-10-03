"""RealChord playlist parser.

This module converts an exported RealChord/iReal-compatible playlist HTML payload
into the stable normalized record consumed by music_intelligence.corpus.realchord.

The parser is intentionally structural: title/composer/style/key, measure
boundaries, sections, time signatures, repeats, endings, navigation markers and
Expected Harmony chord events. It does not attach source/provenance tracking to
the musical record.
"""
from __future__ import annotations

from hashlib import sha1
from html import unescape
import re
from typing import Iterable, Mapping
from urllib.parse import unquote


_MAGIC = "1r34LbKcu7"
_SECTION_RE = re.compile(r"\*([A-DVi])")
_TIMESIG_RE = re.compile(r"T(\d)(\d)")
_ENDING_RE = re.compile(r"N(\d+)")
_STAFF_RE = re.compile(r"<([^>]*)>")
_LINK_RE = re.compile(r'href=["\'](irealb://[^"\']+)["\']', re.IGNORECASE)


def _hussle(value: str) -> str:
    """Symmetric 50-character shuffle used by modern playlist payloads."""
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
    """Decode one modern chart progression payload to its plain grid string."""
    text = payload[len(_MAGIC):] if payload.startswith(_MAGIC) else payload
    text = _hussle(text)
    return text.replace("XyQ", "   ").replace("LZ", " |").replace("Kcl", "| x")


def realchord_id(title: str, composer: str) -> str:
    base = f"{title}|{composer}".strip().casefold().encode("utf-8")
    return "rc_" + sha1(base).hexdigest()[:16]


def _extract_playlist_body(html_or_url: str) -> str:
    text = html_or_url.strip()
    if text.startswith("irealb://"):
        link = text
    else:
        match = _LINK_RE.search(text)
        if not match:
            raise ValueError("No RealChord playlist link found")
        link = unescape(match.group(1))
    return unquote(link[len("irealb://"):])


def parse_playlist_html(html_or_url: str) -> dict[str, object]:
    """Parse a playlist export into normalized RealChord song records."""
    body = _extract_playlist_body(html_or_url)
    parts = body.split("===")
    if len(parts) < 2:
        raise ValueError("Malformed playlist payload")
    playlist_name = parts[-1].strip()
    songs = [parse_song_body(item) for item in parts[:-1] if item.strip()]
    return {
        "schema": "RealChordNormalizedCorpus",
        "schema_version": "1.0",
        "playlist_name": playlist_name,
        "song_count": len(songs),
        "songs": songs,
    }


def parse_song_body(body: str) -> dict[str, object]:
    """Parse one 10-field modern song body."""
    fields = body.split("=")
    if len(fields) < 7:
        raise ValueError("Malformed song body")
    while len(fields) < 10:
        fields.append("")

    title = fields[0].strip()
    composer = fields[1].strip()
    style = fields[3].strip()
    key = fields[4].strip()
    progression = decode_progression(fields[6])
    tempo = int(fields[8]) if fields[8].isdigit() else 0
    repeat_count = int(fields[9]) if fields[9].isdigit() else 0

    measures, warnings = parse_progression(progression)
    return {
        "realchord_id": realchord_id(title, composer),
        "title": title,
        "composer": composer,
        "style": style,
        "key": key,
        "tempo": tempo,
        "repeat_count": repeat_count,
        "measures": measures,
        "parser_warnings": warnings,
    }


def _strip_controls(raw: str) -> str:
    text = _STAFF_RE.sub("", raw)
    text = _SECTION_RE.sub("", text)
    text = _TIMESIG_RE.sub("", text)
    text = _ENDING_RE.sub("", text)
    for token in ("Q", "S", "Y", "U"):
        text = text.replace(token, "")
    return text.strip()


def _split_measures(progression: str) -> list[tuple[str, str, str | None]]:
    """Conservatively split a chart grid while retaining barline semantics."""
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

    # small-size typography controls used in dense cells
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
    """Parse progression text into the normalized RealChord measure contract."""
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
            chord_cells = [(index, token) for index, token in enumerate(cells) if _is_chord(token)]
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
