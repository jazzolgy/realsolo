from fractions import Fraction

from music_intelligence.realsolo_notation_adapter import (
    SharedFormCursorView,
    live_chart_render_model,
)
from music_intelligence.transcribe import (
    ChartMeasure,
    ChordChange,
    ChordChart,
    ChordSymbol,
)


def test_realsolo_live_render_model_uses_external_form_cursor():
    chart = ChordChart(
        "live:render",
        "Live Render",
        (
            ChartMeasure(
                1,
                (ChordChange(Fraction(0), ChordSymbol(0, "maj7")),),
                section="A",
            ),
            ChartMeasure(
                2,
                (
                    ChordChange(Fraction(0), ChordSymbol(2, "m7")),
                    ChordChange(Fraction(2), ChordSymbol(7, "7")),
                ),
                section="B",
            ),
        ),
    )

    model = live_chart_render_model(
        chart,
        SharedFormCursorView(
            "core:render:1",
            measure_number=2,
            beat=Fraction(3),
            occurrence=2,
        ),
        measures_per_row=2,
    )

    assert model.current_measure_number == 2
    assert model.current_chord_label == "G7"
    assert model.current_section == "B"
    assert model.rows[0].measures[1].is_active_measure is True
