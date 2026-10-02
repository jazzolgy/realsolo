"""Renderer-neutral UI projection for live chord-chart clients.

This module converts musical ChordChart semantics into simple immutable cells
and rows.  It contains no drawing toolkit, pixel geometry, or platform code.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .chord_chart import (
    BarlineStyle,
    ChordChart,
    ChordChartPosition,
    EnharmonicPolicy,
    MeasureRepeatKind,
    NavigationMark,
    resolved_measure_chords,
)


@dataclass(frozen=True)
class ChordRenderCell:
    beat: Fraction
    label: str
    is_active: bool = False


@dataclass(frozen=True)
class MeasureRenderCell:
    measure_number: int
    chords: tuple[ChordRenderCell, ...]
    section: str | None = None
    rehearsal_mark: str | None = None
    repeat_start: bool = False
    repeat_end: bool = False
    ending_numbers: tuple[int, ...] = ()
    navigation_marks: tuple[NavigationMark, ...] = ()
    repeat_shorthand: MeasureRepeatKind = MeasureRepeatKind.NONE
    barline: BarlineStyle = BarlineStyle.NORMAL
    is_active_measure: bool = False


@dataclass(frozen=True)
class ChordChartRenderRow:
    row_index: int
    measures: tuple[MeasureRenderCell, ...]


@dataclass(frozen=True)
class ChordChartRenderModel:
    chart_id: str
    title: str
    meter_numerator: int
    meter_denominator: int
    rows: tuple[ChordChartRenderRow, ...]
    current_measure_number: int | None = None
    current_beat: Fraction | None = None
    current_chord_label: str | None = None
    next_chord_label: str | None = None
    current_section: str | None = None
    transpose_semitones: int = 0


def _active_chord_index(
    chart: ChordChart,
    *,
    measure_number: int,
    beat: Fraction,
) -> int | None:
    chords = resolved_measure_chords(chart, measure_number)
    active: int | None = None
    for index, change in enumerate(chords):
        if change.beat <= beat:
            active = index
        else:
            break
    return active


def build_chord_chart_render_model(
    chart: ChordChart,
    *,
    position: ChordChartPosition | None = None,
    measures_per_row: int = 4,
    transpose_semitones: int = 0,
    enharmonic_policy: EnharmonicPolicy | None = None,
) -> ChordChartRenderModel:
    """Project a chart into rows/cells suitable for any UI renderer."""

    chart.validate()
    display_chart = (
        chart.transpose(
            transpose_semitones,
            enharmonic_policy=enharmonic_policy,
        )
        if transpose_semitones or enharmonic_policy is not None
        else chart
    )
    if measures_per_row <= 0:
        raise ValueError("measures_per_row must be positive")

    active_index: int | None = None
    if position is not None:
        if not 1 <= position.measure_number <= len(chart.measures):
            raise ValueError("position measure outside chart")
        if position.beat < 0 or position.beat >= chart.beats_per_bar:
            raise ValueError("position beat outside measure")
        active_index = _active_chord_index(
            chart,
            measure_number=position.measure_number,
            beat=position.beat,
        )

    measure_cells: list[MeasureRenderCell] = []
    for measure in display_chart.measures:
        resolved = resolved_measure_chords(display_chart, measure.number)
        is_active_measure = (
            position is not None and measure.number == position.measure_number
        )
        chord_cells = tuple(
            ChordRenderCell(
                beat=change.beat,
                label=change.chord.display(),
                is_active=(
                    is_active_measure
                    and active_index is not None
                    and index == active_index
                ),
            )
            for index, change in enumerate(resolved)
        )
        measure_cells.append(
            MeasureRenderCell(
                measure_number=measure.number,
                chords=chord_cells,
                section=measure.section,
                rehearsal_mark=measure.rehearsal_mark,
                repeat_start=measure.repeat_start,
                repeat_end=measure.repeat_end,
                ending_numbers=measure.ending_numbers,
                navigation_marks=measure.navigation_marks,
                repeat_shorthand=measure.repeat_shorthand,
                barline=measure.barline,
                is_active_measure=is_active_measure,
            )
        )

    rows = tuple(
        ChordChartRenderRow(
            row_index=index // measures_per_row,
            measures=tuple(measure_cells[index:index + measures_per_row]),
        )
        for index in range(0, len(measure_cells), measures_per_row)
    )

    return ChordChartRenderModel(
        chart_id=chart.chart_id,
        title=chart.title,
        meter_numerator=chart.meter_numerator,
        meter_denominator=chart.meter_denominator,
        rows=rows,
        current_measure_number=position.measure_number if position else None,
        current_beat=position.beat if position else None,
        current_chord_label=(
            position.active_chord.transpose(
                transpose_semitones,
                enharmonic_policy=enharmonic_policy,
            ).display()
            if position is not None and position.active_chord is not None
            else None
        ),
        next_chord_label=(
            position.next_chord.transpose(
                transpose_semitones,
                enharmonic_policy=enharmonic_policy,
            ).display()
            if position is not None and position.next_chord is not None
            else None
        ),
        current_section=position.section if position else None,
        transpose_semitones=transpose_semitones,
    )
