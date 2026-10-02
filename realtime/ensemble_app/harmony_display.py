from __future__ import annotations

import re

NOTE_TO_PC = {
    "C": 0, "B#": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4, "E#": 5, "F": 5, "F#": 6, "Gb": 6, "G": 7,
    "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11, "Cb": 11,
}
SHARP_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
FLAT_NAMES = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
ROOT_RE = re.compile(r"^([A-G](?:#|b)?)(.*)$")


def _transpose_note(note: str, semitones: int, *, prefer_flats: bool) -> str:
    pc = NOTE_TO_PC.get(note)
    if pc is None:
        return note
    names = FLAT_NAMES if prefer_flats else SHARP_NAMES
    return names[(pc + semitones) % 12]


def transpose_chord(symbol: str, semitones: int) -> str:
    if not symbol or symbol in {"N.C.", "NC", "%"} or semitones % 12 == 0:
        return symbol

    main, slash, bass = symbol.partition("/")
    match = ROOT_RE.match(main)
    if not match:
        return symbol

    root, suffix = match.groups()
    prefer_flats = "b" in root or (slash and "b" in bass)
    transposed = _transpose_note(root, semitones, prefer_flats=prefer_flats) + suffix

    if slash:
        bass_match = ROOT_RE.match(bass)
        if bass_match:
            bass_root, bass_suffix = bass_match.groups()
            transposed += "/" + _transpose_note(
                bass_root, semitones, prefer_flats=prefer_flats
            ) + bass_suffix
        else:
            transposed += "/" + bass
    return transposed
