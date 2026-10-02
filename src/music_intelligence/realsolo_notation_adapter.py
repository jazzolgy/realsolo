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
    ChordChartPosition,
    ChordSymbol,
    EnharmonicPolicy,
    MeasureRepeatKind,
    NavigationMark,
    chart_position,
    parse_chord_symbol,
)
from music_intelligence.transcribe.chord_chart_render import (
    ChordChartRenderModel,
    build_chord_chart_render_model,
)
from music_intelligence.transcribe.chord_chart_viewport import (
    ChordChartViewport,
    ChordChartViewportConfig,
    build_chord_chart_viewport,
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


@dataclass(frozen=True)
class SharedFormCursorView:
    """Temporary adapter shape until CCR-TRANSCRIBE-002 is adopted."""

    form_state_id: str
    measure_number: int
    beat: Fraction
    occurrence: int = 1
    active_ending: int | None = None

    def validate(self) -> None:
        if not self.form_state_id:
            raise ValueError("form_state_id is required")
        if self.measure_number < 1:
            raise ValueError("measure_number must be positive")
        if self.beat < 0:
            raise ValueError("beat may not be negative")
        if self.occurrence < 1:
            raise ValueError("occurrence must be positive")


@dataclass(frozen=True)
class LiveChordChartState:
    form_state_id: str
    occurrence: int
    active_ending: int | None
    position: ChordChartPosition


def live_chart_state(
    chart: ChordChart,
    cursor: SharedFormCursorView,
) -> LiveChordChartState:
    """Map an authoritative external form cursor to chart presentation state."""

    cursor.validate()
    position = chart_position(
        chart,
        measure_number=cursor.measure_number,
        beat=cursor.beat,
    )
    return LiveChordChartState(
        form_state_id=cursor.form_state_id,
        occurrence=cursor.occurrence,
        active_ending=cursor.active_ending,
        position=position,
    )


def live_chart_render_model(
    chart: ChordChart,
    cursor: SharedFormCursorView,
    *,
    measures_per_row: int = 4,
    transpose_semitones: int = 0,
) -> ChordChartRenderModel:
    """Build the complete renderer-neutral live chart projection."""

    state = live_chart_state(chart, cursor)
    return build_chord_chart_render_model(
        chart,
        position=state.position,
        measures_per_row=measures_per_row,
        transpose_semitones=transpose_semitones,
    )


def live_chart_viewport(
    chart: ChordChart,
    cursor: SharedFormCursorView,
    *,
    measures_per_row: int = 4,
    transpose_semitones: int = 0,
    viewport_config: ChordChartViewportConfig = ChordChartViewportConfig(),
    previous: ChordChartViewport | None = None,
    previous_section: str | None = None,
) -> ChordChartViewport:
    """Build the live auto-follow viewport from an authoritative form cursor."""

    model = live_chart_render_model(
        chart,
        cursor,
        measures_per_row=measures_per_row,
        transpose_semitones=transpose_semitones,
    )
    return build_chord_chart_viewport(
        model,
        config=viewport_config,
        previous=previous,
        previous_section=previous_section,
    )


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
