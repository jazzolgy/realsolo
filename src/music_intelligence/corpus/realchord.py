"""RealChord 1350 Shared symbolic-corpus contract."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from .canonical_coordinate import CanonicalMusicalCoordinate


@dataclass(frozen=True)
class RealChordChordEvent:
    beat: float
    symbol: str
    duration_beats: float | None = None

    def validate(self) -> None:
        if self.beat < 0:
            raise ValueError("beat may not be negative")
        if not self.symbol.strip():
            raise ValueError("symbol is required")


@dataclass(frozen=True)
class RealChordMeasure:
    measure_in_form: int
    section: str
    measure_in_section: int
    chords: tuple[RealChordChordEvent,...]
    repeat_start: bool = False
    repeat_end: bool = False
    ending: int | None = None

    def validate(self) -> None:
        if self.measure_in_form < 1 or self.measure_in_section < 1:
            raise ValueError("measure numbers are 1-based")
        if not self.section:
            raise ValueError("section is required")
        for chord in self.chords:
            chord.validate()


@dataclass(frozen=True)
class RealChordSong:
    realchord_id: int
    title: str
    composer: str
    style: str
    key: str
    measures: tuple[RealChordMeasure,...]
    raw_chart: str = ""
    provenance: tuple[str,...] = ()

    def validate(self) -> None:
        if self.realchord_id <= 0:
            raise ValueError("realchord_id must be positive")
        if not self.title.strip():
            raise ValueError("title is required")
        for measure in self.measures:
            measure.validate()

    def measure_at(self, measure_in_form: int) -> RealChordMeasure:
        return next(x for x in self.measures if x.measure_in_form==measure_in_form)

    def expected_chord_at(self, coordinate: CanonicalMusicalCoordinate) -> RealChordChordEvent | None:
        coordinate.validate()
        if coordinate.realchord_id != self.realchord_id:
            raise ValueError("coordinate belongs to another RealChord song")
        measure=self.measure_at(coordinate.measure_in_form)
        active=[x for x in measure.chords if x.beat <= coordinate.beat]
        return active[-1] if active else (measure.chords[0] if measure.chords else None)


def expected_harmony_frame(
    song: RealChordSong,
    coordinate: CanonicalMusicalCoordinate,
    *,
    observed: HarmonicEvidence | None=None,
    inferred: HarmonicEvidence | None=None,
) -> HarmonicFrame:
    """Use RealChord only as Expected Harmony.

    Observed and inferred evidence remain independent channels.
    """
    chord=song.expected_chord_at(coordinate)
    expected=(
        HarmonicEvidence(
            source=HarmonySource.EXPECTED,
            symbol=chord.symbol,
            local_key=song.key or None,
            confidence=1.0,
            provenance=(
                f"realchord:{song.realchord_id}",
                coordinate.section,
                f"measure:{coordinate.measure_in_form}",
                f"beat:{coordinate.beat}",
            ),
        )
        if chord is not None else None
    )
    frame=HarmonicFrame(expected=expected,observed=observed,inferred=inferred)
    frame.validate()
    return frame
