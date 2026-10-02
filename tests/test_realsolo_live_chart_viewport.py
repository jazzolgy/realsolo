from fractions import Fraction

from music_intelligence.realsolo_notation_adapter import (
    SharedFormCursorView,
    live_chart_viewport,
)
from music_intelligence.transcribe import (
    ChartMeasure,
    ChordChange,
    ChordChart,
    ChordSymbol,
)


def test_realsolo_live_viewport_uses_core_cursor_without_executing_form():
    chart = ChordChart(
        "live:viewport",
        "Live Viewport",
        tuple(
            ChartMeasure(
                i,
                (ChordChange(Fraction(0), ChordSymbol((i + 4) % 12, "7")),),
                section="A" if i <= 4 else "B",
            )
            for i in range(1, 9)
        ),
    )

    viewport = live_chart_viewport(
        chart,
        SharedFormCursorView(
            form_state_id="core:view:2",
            measure_number=6,
            beat=Fraction(1),
            occurrence=2,
        ),
        measures_per_row=4,
    )

    assert viewport.active_row_index == 1
    assert viewport.follow_target_row_index == 1
    assert [r.row_index for r in viewport.visible_rows] == [0, 1]
