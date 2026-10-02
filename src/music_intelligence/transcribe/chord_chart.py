"""Form-aware chord chart model for RealSolo performance views.

This is a source-neutral musical representation, not an iReal Pro file-format
implementation.  It models common chord-chart semantics so the same data can
drive RealSolo's live chart UI, a printable lead sheet, or future exporters.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
import re


class BarlineStyle(str, Enum):
    NORMAL = "normal"
    DOUBLE = "double"
    FINAL = "final"


class EnharmonicPolicy(str, Enum):
    AUTO = "auto"
    PREFER_FLATS = "prefer_flats"
    PREFER_SHARPS = "prefer_sharps"


class MeasureRepeatKind(str, Enum):
    NONE = "none"
    ONE_BAR = "one_bar"
    TWO_BAR = "two_bar"


class NavigationMark(str, Enum):
    SEGNO = "segno"
    CODA = "coda"
    TO_CODA = "to_coda"
    DC = "dc"
    DS = "ds"
    FINE = "fine"


@dataclass(frozen=True)
class ChordSymbol:
    """Display-oriented chord identity with transposable root/bass."""

    root_pc: int | None
    quality: str = ""
    bass_pc: int | None = None
    no_chord: bool = False
    enharmonic_policy: EnharmonicPolicy = EnharmonicPolicy.AUTO

    def validate(self) -> None:
        if self.no_chord:
            if self.root_pc is not None or self.bass_pc is not None:
                raise ValueError("N.C. may not carry root or bass")
            return
        if self.root_pc is None:
            raise ValueError("chord requires root_pc unless no_chord")
        if not 0 <= self.root_pc <= 11:
            raise ValueError("root_pc must be within 0..11")
        if self.bass_pc is not None and not 0 <= self.bass_pc <= 11:
            raise ValueError("bass_pc must be within 0..11")

    def transpose(self, semitones: int) -> "ChordSymbol":
        self.validate()
        if self.no_chord:
            return self
        return ChordSymbol(
            root_pc=(self.root_pc + semitones) % 12,
            quality=self.quality,
            bass_pc=(
                (self.bass_pc + semitones) % 12
                if self.bass_pc is not None
                else None
            ),
            no_chord=False,
            enharmonic_policy=self.enharmonic_policy,
        )

    def display(self) -> str:
        self.validate()
        if self.no_chord:
            return "N.C."
        sharp_names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
        flat_names = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
        names = (
            sharp_names
            if self.enharmonic_policy is EnharmonicPolicy.PREFER_SHARPS
            else flat_names
        )
        text = names[self.root_pc] + self.quality
        if self.bass_pc is not None:
            text += "/" + names[self.bass_pc]
        return text


_NOTE_TO_PC = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}


def parse_chord_symbol(label: str) -> ChordSymbol:
    """Parse a practical chord-chart label while preserving arbitrary suffix.

    Root and optional slash bass are structured for transposition.  The quality
    suffix remains verbatim so jazz extensions/alterations do not require a
    closed vocabulary.
    """

    text = label.strip()
    if text.upper().replace(" ", "") in {"NC", "N.C.", "N.C"}:
        return ChordSymbol(None, no_chord=True)

    match = re.fullmatch(
        r"([A-G](?:#|b)?)(.*?)(?:/([A-G](?:#|b)?))?",
        text,
    )
    if match is None:
        raise ValueError(f"unsupported chord symbol: {label!r}")

    root_name, quality, bass_name = match.groups()
    if root_name not in _NOTE_TO_PC:
        raise ValueError(f"unsupported chord root: {root_name}")

    accidental_tokens = root_name + (bass_name or "")
    if "#" in accidental_tokens:
        policy = EnharmonicPolicy.PREFER_SHARPS
    elif "b" in accidental_tokens:
        policy = EnharmonicPolicy.PREFER_FLATS
    else:
        policy = EnharmonicPolicy.AUTO

    chord = ChordSymbol(
        root_pc=_NOTE_TO_PC[root_name],
        quality=quality,
        bass_pc=_NOTE_TO_PC[bass_name] if bass_name else None,
        enharmonic_policy=policy,
    )
    chord.validate()
    return chord


@dataclass(frozen=True)
class ChordChange:
    beat: Fraction
    chord: ChordSymbol

    def validate(self, beats_per_bar: Fraction) -> None:
        if self.beat < 0 or self.beat >= beats_per_bar:
            raise ValueError("chord beat must fall within measure")
        self.chord.validate()


@dataclass(frozen=True)
class ChartMeasure:
    number: int
    chords: tuple[ChordChange, ...]
    section: str | None = None
    rehearsal_mark: str | None = None
    repeat_start: bool = False
    repeat_end: bool = False
    ending_numbers: tuple[int, ...] = ()
    navigation_marks: tuple[NavigationMark, ...] = ()
    repeat_shorthand: MeasureRepeatKind = MeasureRepeatKind.NONE
    barline: BarlineStyle = BarlineStyle.NORMAL

    def validate(self, beats_per_bar: Fraction) -> None:
        if self.number <= 0:
            raise ValueError("measure number must be positive")
        if len(set(self.ending_numbers)) != len(self.ending_numbers):
            raise ValueError("ending numbers must be unique")
        if self.repeat_shorthand is not MeasureRepeatKind.NONE and self.chords:
            raise ValueError("repeat-shorthand measure may not redefine chords")
        previous: Fraction | None = None
        for change in self.chords:
            change.validate(beats_per_bar)
            if previous is not None and change.beat <= previous:
                raise ValueError("chord changes must be strictly ordered")
            previous = change.beat


@dataclass(frozen=True)
class ChordChart:
    chart_id: str
    title: str
    measures: tuple[ChartMeasure, ...]
    meter_numerator: int = 4
    meter_denominator: int = 4
    key_fifths: int | None = None
    provenance: tuple[str, ...] = ()

    @property
    def beats_per_bar(self) -> Fraction:
        return Fraction(self.meter_numerator * 4, self.meter_denominator)

    def validate(self) -> None:
        if not self.chart_id or not self.title:
            raise ValueError("chart identity is required")
        if self.meter_numerator <= 0 or self.meter_denominator <= 0:
            raise ValueError("meter must be positive")
        if not self.measures:
            raise ValueError("chart requires measures")
        numbers = [measure.number for measure in self.measures]
        if numbers != list(range(1, len(self.measures) + 1)):
            raise ValueError("chart measures must be sequential")
        for measure in self.measures:
            measure.validate(self.beats_per_bar)

    def transpose(self, semitones: int) -> "ChordChart":
        self.validate()
        measures = tuple(
            ChartMeasure(
                number=m.number,
                chords=tuple(
                    ChordChange(c.beat, c.chord.transpose(semitones))
                    for c in m.chords
                ),
                section=m.section,
                rehearsal_mark=m.rehearsal_mark,
                repeat_start=m.repeat_start,
                repeat_end=m.repeat_end,
                ending_numbers=m.ending_numbers,
                navigation_marks=m.navigation_marks,
                repeat_shorthand=m.repeat_shorthand,
                barline=m.barline,
            )
            for m in self.measures
        )
        return ChordChart(
            chart_id=f"{self.chart_id}:transpose:{semitones}",
            title=self.title,
            measures=measures,
            meter_numerator=self.meter_numerator,
            meter_denominator=self.meter_denominator,
            key_fifths=None,
            provenance=self.provenance + ("transcribe:chord-chart-transpose",),
        )


@dataclass(frozen=True)
class ChordChartPosition:
    measure_number: int
    beat: Fraction
    section: str | None
    active_chord: ChordSymbol | None
    next_chord: ChordSymbol | None


def chart_position(
    chart: ChordChart,
    *,
    measure_number: int,
    beat: Fraction,
) -> ChordChartPosition:
    """Resolve the live-performance cursor for a chart position."""

    chart.validate()
    if not 1 <= measure_number <= len(chart.measures):
        raise ValueError("measure_number outside chart")
    if beat < 0 or beat >= chart.beats_per_bar:
        raise ValueError("beat outside measure")

    measure = chart.measures[measure_number - 1]
    active: ChordSymbol | None = None
    next_chord: ChordSymbol | None = None

    for change in measure.chords:
        if change.beat <= beat:
            active = change.chord
        elif next_chord is None:
            next_chord = change.chord
            break

    if active is None:
        for prior_measure in reversed(chart.measures[: measure_number - 1]):
            if prior_measure.chords:
                active = prior_measure.chords[-1].chord
                break

    if next_chord is None:
        for later_measure in chart.measures[measure_number:]:
            if later_measure.chords:
                next_chord = later_measure.chords[0].chord
                break

    return ChordChartPosition(
        measure_number=measure_number,
        beat=beat,
        section=measure.section,
        active_chord=active,
        next_chord=next_chord,
    )
