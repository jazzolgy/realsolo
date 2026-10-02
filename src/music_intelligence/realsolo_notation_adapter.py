"""RealSolo integration adapter from Shared Harmony into ChordChart.

This module is intentionally outside the reusable transcribe package boundary:
it may import Shared Harmony and translate it into the source-neutral chart
model consumed by NotationEngine and UI layers.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import ceil
from typing import Mapping, Sequence

from music_intelligence.harmony.harmonic_time import HarmonicSpan
from music_intelligence.transcribe.chord_chart import (
    BarlineStyle,
    ChartMeasure,
    ChordChange,
    ChordChart,
    ChordSymbol,
    EnharmonicPolicy,
    MeasureRepeatKind,
    NavigationMark,
    parse_chord_symbol,
)


@dataclass(frozen=True)
class ChartFormMeasure:
    section: str | None = None
    rehearsal_mark: str | None = None
    repeat_start: bool = False
    repeat_end: bool = False
    ending_numbers: tuple[int, ...] = ()
    navigation_marks: tuple[NavigationMark, ...] = ()
    repeat_shorthand: MeasureRepeatKind = MeasureRepeatKind.NONE
    barline: BarlineStyle = BarlineStyle.NORMAL


def _symbol_from_span(span: HarmonicSpan) -> ChordSymbol:
    span.validate()
    if span.symbol:
        parsed = parse_chord_symbol(span.symbol)
        if span.root_pc is None or parsed.no_chord or parsed.root_pc == span.root_pc:
            return parsed
        return ChordSymbol(
            root_pc=span.root_pc,
            quality=parsed.quality,
            bass_pc=parsed.bass_pc,
            no_chord=False,
            enharmonic_policy=parsed.enharmonic_policy,
        )
    if span.root_pc is None:
        return ChordSymbol(None, no_chord=True)
    return ChordSymbol(
        span.root_pc,
        enharmonic_policy=EnharmonicPolicy.AUTO,
    )


def chord_chart_from_harmonic_spans(
    spans: Sequence[HarmonicSpan],
    *,
    chart_id: str,
    title: str,
    meter_numerator: int = 4,
    meter_denominator: int = 4,
    form_by_measure: Mapping[int, ChartFormMeasure] | None = None,
) -> ChordChart:
    """Project Shared Harmony timing into a compact live-performance chart."""

    if meter_numerator <= 0 or meter_denominator <= 0:
        raise ValueError("meter must be positive")
    if not spans:
        raise ValueError("harmonic spans are required")

    beats_per_bar = Fraction(meter_numerator * 4, meter_denominator)
    ordered = sorted(spans, key=lambda x: x.start_beat)
    for span in ordered:
        span.validate()
        if span.start_beat < 0:
            raise ValueError("harmonic span start may not be negative")

    total_beats = max(span.start_beat + span.duration_beats for span in ordered)
    measure_count = max(1, ceil(float(Fraction(str(total_beats)) / beats_per_bar)))
    changes: dict[int, list[ChordChange]] = {i: [] for i in range(1, measure_count + 1)}

    provenance: list[str] = ["realsolo:shared-harmony-chart-projection"]
    for span in ordered:
        start = Fraction(str(span.start_beat))
        measure_number = int(start // beats_per_bar) + 1
        beat = start - (measure_number - 1) * beats_per_bar
        changes[measure_number].append(
            ChordChange(beat=beat, chord=_symbol_from_span(span))
        )
        provenance.extend(span.provenance)

    form_by_measure = form_by_measure or {}
    measures: list[ChartMeasure] = []
    for number in range(1, measure_count + 1):
        meta = form_by_measure.get(number, ChartFormMeasure())
        measure_changes = tuple(sorted(changes[number], key=lambda c: c.beat))
        if meta.repeat_shorthand is not MeasureRepeatKind.NONE:
            measure_changes = ()
        measures.append(
            ChartMeasure(
                number=number,
                chords=measure_changes,
                section=meta.section,
                rehearsal_mark=meta.rehearsal_mark,
                repeat_start=meta.repeat_start,
                repeat_end=meta.repeat_end,
                ending_numbers=meta.ending_numbers,
                navigation_marks=meta.navigation_marks,
                repeat_shorthand=meta.repeat_shorthand,
                barline=meta.barline,
            )
        )

    chart = ChordChart(
        chart_id=chart_id,
        title=title,
        measures=tuple(measures),
        meter_numerator=meter_numerator,
        meter_denominator=meter_denominator,
        provenance=tuple(dict.fromkeys(provenance)),
    )
    chart.validate()
    return chart
