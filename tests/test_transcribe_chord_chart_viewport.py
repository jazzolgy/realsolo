from fractions import Fraction

from music_intelligence.transcribe import (
    ChartMeasure,
    ChordChange,
    ChordChart,
    ChordSymbol,
    chart_position,
)
from music_intelligence.transcribe.chord_chart_render import build_chord_chart_render_model
from music_intelligence.transcribe.chord_chart_viewport import (
    ChordChartViewportConfig,
    build_chord_chart_viewport,
)


def _chart():
    return ChordChart(
        "viewport:1",
        "Viewport",
        tuple(
            ChartMeasure(
                i,
                (ChordChange(Fraction(0), ChordSymbol((i - 1) % 12, "7")),),
                section="A" if i <= 8 else "B",
            )
            for i in range(1, 13)
        ),
    )


def test_viewport_tracks_active_row_and_prefetches_neighbors():
    chart = _chart()
    position = chart_position(chart, measure_number=6, beat=Fraction(1))
    model = build_chord_chart_render_model(chart, position=position, measures_per_row=4)

    viewport = build_chord_chart_viewport(
        model,
        config=ChordChartViewportConfig(
            visible_row_count=2,
            prefetch_before=1,
            prefetch_after=1,
            keep_current_row_slot=0,
        ),
    )

    assert viewport.active_row_index == 1
    assert [r.row_index for r in viewport.visible_rows] == [1, 2]
    assert [r.row_index for r in viewport.prefetched_rows] == [0, 1, 2]


def test_viewport_reports_row_advance_and_section_change():
    chart = _chart()

    first = build_chord_chart_viewport(
        build_chord_chart_render_model(
            chart,
            position=chart_position(chart, measure_number=8, beat=Fraction(3)),
            measures_per_row=4,
        )
    )
    second_model = build_chord_chart_render_model(
        chart,
        position=chart_position(chart, measure_number=9, beat=Fraction(0)),
        measures_per_row=4,
    )
    second = build_chord_chart_viewport(
        second_model,
        previous=first,
        previous_section="A",
    )

    assert first.active_row_index == 1
    assert second.active_row_index == 2
    assert second.should_advance is True
    assert second.section_changed is True


def test_viewport_keeps_last_rows_visible_near_chart_end():
    chart = _chart()
    model = build_chord_chart_render_model(
        chart,
        position=chart_position(chart, measure_number=12, beat=Fraction(1)),
        measures_per_row=4,
    )

    viewport = build_chord_chart_viewport(
        model,
        config=ChordChartViewportConfig(visible_row_count=2),
    )

    assert [r.row_index for r in viewport.visible_rows] == [1, 2]
    assert viewport.follow_target_row_index == 2
