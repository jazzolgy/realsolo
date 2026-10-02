"""Page-level scorebook ingestion for scanned lead sheets.

This module converts reviewed page observations into a source-neutral
ChordChart draft plus non-chart evidence (style, feel changes, bass instructions
and provenance). It does not perform OCR itself and it does not infer player
generation policy.

A vision/manual extraction layer supplies observations. This module validates
them and compiles only what the page evidence explicitly supports.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

from .chord_chart import (
    BarlineStyle,
    ChartMeasure,
    ChordChange,
    ChordChart,
    ChordSymbol,
    NavigationMark,
)


@dataclass(frozen=True)
class ObservedChord:
    measure: int
    beat: Fraction
    root_pc: int | None
    quality: str = ""
    bass_pc: int | None = None
    no_chord: bool = False
    preferred_sharps: bool = False
    confidence: float = 1.0

    def validate(self) -> None:
        if self.measure < 1:
            raise ValueError("measure must be positive")
        if self.beat < 0:
            raise ValueError("beat may not be negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        ChordSymbol(
            self.root_pc,
            self.quality,
            self.bass_pc,
            self.no_chord,
            self.preferred_sharps,
        ).validate()


@dataclass(frozen=True)
class ObservedMeasure:
    number: int
    section: str | None = None
    rehearsal_mark: str | None = None
    repeat_start: bool = False
    repeat_end: bool = False
    ending_numbers: tuple[int, ...] = ()
    navigation_marks: tuple[NavigationMark, ...] = ()
    barline: BarlineStyle = BarlineStyle.NORMAL


@dataclass(frozen=True)
class PageAnnotation:
    kind: str
    value: str
    page: int
    confidence: float = 1.0

    def validate(self) -> None:
        if not self.kind.strip() or not self.value.strip():
            raise ValueError("annotation kind/value required")
        if self.page < 1:
            raise ValueError("page must be 1-based")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class ScorebookPageObservation:
    source_book_id: str
    song_id: str
    title: str
    pages: tuple[int, ...]
    meter_numerator: int
    meter_denominator: int
    measures: tuple[ObservedMeasure, ...]
    chords: tuple[ObservedChord, ...]
    annotations: tuple[PageAnnotation, ...] = ()
    key_fifths: int | None = None
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.source_book_id or not self.song_id or not self.title:
            raise ValueError("source_book_id/song_id/title required")
        if not self.pages or any(x < 1 for x in self.pages):
            raise ValueError("one or more 1-based pages required")
        if self.meter_numerator <= 0 or self.meter_denominator <= 0:
            raise ValueError("meter must be positive")
        if not self.measures:
            raise ValueError("at least one measure observation required")
        nums=[x.number for x in self.measures]
        if nums != list(range(1, len(nums)+1)):
            raise ValueError("observed measures must be sequential")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        for x in self.chords:
            x.validate()
            if x.measure > len(self.measures):
                raise ValueError("chord references unknown measure")
        for x in self.annotations:
            x.validate()
            if x.page not in self.pages:
                raise ValueError("annotation page outside observation span")


@dataclass(frozen=True)
class ScorebookIngestionResult:
    chart: ChordChart
    annotations: tuple[PageAnnotation, ...]
    source_book_id: str
    source_pages: tuple[int, ...]
    observation_confidence: float

    def annotations_of(self, kind: str) -> tuple[PageAnnotation, ...]:
        return tuple(x for x in self.annotations if x.kind == kind)


def compile_scorebook_observation(
    observation: ScorebookPageObservation,
) -> ScorebookIngestionResult:
    """Compile explicit page evidence into a ChordChart.

    No missing harmony, key, form or chords are filled from general jazz
    knowledge. If the observation did not support a fact, the result leaves it
    absent.
    """
    observation.validate()
    beats_per_bar = Fraction(
        observation.meter_numerator * 4,
        observation.meter_denominator,
    )

    by_measure: dict[int, list[ObservedChord]] = {
        m.number: [] for m in observation.measures
    }
    for chord in observation.chords:
        if chord.beat >= beats_per_bar:
            raise ValueError("observed chord lies outside measure")
        by_measure[chord.measure].append(chord)

    measures: list[ChartMeasure] = []
    for meta in observation.measures:
        changes = tuple(
            ChordChange(
                beat=x.beat,
                chord=ChordSymbol(
                    root_pc=x.root_pc,
                    quality=x.quality,
                    bass_pc=x.bass_pc,
                    no_chord=x.no_chord,
                    preferred_sharps=x.preferred_sharps,
                ),
            )
            for x in sorted(by_measure[meta.number], key=lambda x: x.beat)
        )
        measures.append(ChartMeasure(
            number=meta.number,
            chords=changes,
            section=meta.section,
            rehearsal_mark=meta.rehearsal_mark,
            repeat_start=meta.repeat_start,
            repeat_end=meta.repeat_end,
            ending_numbers=meta.ending_numbers,
            navigation_marks=meta.navigation_marks,
            barline=meta.barline,
        ))

    chart = ChordChart(
        chart_id=f"scorebook:{observation.song_id}",
        title=observation.title,
        measures=tuple(measures),
        meter_numerator=observation.meter_numerator,
        meter_denominator=observation.meter_denominator,
        key_fifths=observation.key_fifths,
        provenance=observation.provenance + (
            f"scorebook:{observation.source_book_id}",
            "transcribe:scorebook-page-observation",
        ),
    )
    chart.validate()
    return ScorebookIngestionResult(
        chart=chart,
        annotations=observation.annotations,
        source_book_id=observation.source_book_id,
        source_pages=observation.pages,
        observation_confidence=observation.confidence,
    )


def evidence_summary(result: ScorebookIngestionResult) -> dict[str, tuple[str, ...]]:
    """Return compact non-musical evidence for Core/Player adapters."""
    out: dict[str, list[str]] = {}
    for item in result.annotations:
        out.setdefault(item.kind, []).append(item.value)
    return {k: tuple(v) for k, v in out.items()}
