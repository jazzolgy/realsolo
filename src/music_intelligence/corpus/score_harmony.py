"""Bridge explicit score chord evidence into Expected Harmony.

This module parses only concrete chord symbols already present in structured
score evidence. It does not infer local key, function, reharmonization, or
navigation order.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)

from .score_context import ScoreContextSnapshot


_ROOT_PC = {
    "C": 0, "C#": 1, "Db": 1,
    "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4, "E#": 5,
    "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8,
    "A": 9, "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11, "B#": 0,
}
_CHORD_RE = re.compile(r"^([A-G])([b#]?)([^/]*)(?:/([A-G])([b#]?))?$")


class UnsupportedScoreChord(ValueError):
    pass


@dataclass(frozen=True)
class ParsedScoreChord:
    symbol: str
    root_pc: int
    pitch_classes: frozenset[int]
    bass_pc: int | None = None
    quality: str = ""


def parse_score_chord_symbol(symbol: str) -> ParsedScoreChord:
    token = symbol.strip()
    match = _CHORD_RE.match(token)
    if not match:
        raise UnsupportedScoreChord(f"unsupported score chord: {symbol!r}")

    root_name = match.group(1) + match.group(2)
    suffix = match.group(3)
    bass_name = (
        match.group(4) + match.group(5)
        if match.group(4) is not None
        else None
    )
    root = _ROOT_PC.get(root_name)
    bass = _ROOT_PC.get(bass_name) if bass_name is not None else None
    if root is None or (bass_name is not None and bass is None):
        raise UnsupportedScoreChord(f"unsupported chord spelling: {symbol!r}")

    low = suffix.lower()
    if low in {"maj7", "ma7"}:
        intervals = (0, 4, 7, 11)
        quality = "major7"
    elif low in {"m7b5", "min7b5", "mi7b5"}:
        intervals = (0, 3, 6, 10)
        quality = "half_diminished7"
    elif low in {"m9", "min9", "mi9"}:
        intervals = (0, 2, 3, 7, 10)
        quality = "minor9"
    elif low in {"m7", "min7", "mi7"}:
        intervals = (0, 3, 7, 10)
        quality = "minor7"
    elif low in {"7#9", "7(#9)"}:
        intervals = (0, 3, 4, 7, 10)
        quality = "dominant7_sharp9"
    elif low == "7":
        intervals = (0, 4, 7, 10)
        quality = "dominant7"
    else:
        raise UnsupportedScoreChord(f"unsupported score chord quality: {symbol!r}")

    pcs = frozenset((root + i) % 12 for i in intervals)
    return ParsedScoreChord(token, root, pcs, bass, quality)


def expected_harmony_from_score(
    snapshot: ScoreContextSnapshot,
) -> HarmonicEvidence | None:
    """Return Expected Harmony only when one explicit chord is active."""
    if len(snapshot.chords) != 1:
        return None
    parsed = parse_score_chord_symbol(snapshot.chords[0])
    out = HarmonicEvidence(
        source=HarmonySource.EXPECTED,
        symbol=parsed.symbol,
        root_pc=parsed.root_pc,
        pitch_classes=parsed.pitch_classes,
        confidence=snapshot.confidence,
        provenance=tuple(dict.fromkeys(
            snapshot.provenance + ("structured_score_chord",)
        )),
    )
    out.validate()
    return out


def harmonic_frame_from_score(
    current: ScoreContextSnapshot,
    *,
    next_snapshot: ScoreContextSnapshot | None = None,
    phrase_position: float = 0.0,
    tension: float = 0.0,
    cadence_state: str = "open",
) -> HarmonicFrame:
    """Build a score-backed frame without inventing harmonic interpretation."""
    if not 0.0 <= phrase_position <= 1.0:
        raise ValueError("phrase_position must be within 0..1")
    if not 0.0 <= tension <= 1.0:
        raise ValueError("tension must be within 0..1")

    frame = HarmonicFrame(
        expected=expected_harmony_from_score(current),
        next_expected=(
            expected_harmony_from_score(next_snapshot)
            if next_snapshot is not None
            else None
        ),
        phrase_position=phrase_position,
        tension=tension,
        cadence_state=cadence_state,
    )
    frame.validate()
    return frame
