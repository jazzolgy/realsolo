from fractions import Fraction

from music_intelligence.realsolo_notation_adapter import (
    SharedFormCursorView,
    live_chart_state,
)
from music_intelligence.transcribe import (
    ChartMeasure,
    ChordChange,
    ChordChart,
    ChordSymbol,
)


def test_live_chart_uses_authoritative_external_form_cursor():
    chart = ChordChart(
        "form:live",
        "Form Live",
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
    cursor = SharedFormCursorView(
        form_state_id="core:form:77",
        measure_number=2,
        beat=Fraction(3),
        occurrence=3,
        active_ending=2,
    )

    state = live_chart_state(chart, cursor)

    assert state.form_state_id == "core:form:77"
    assert state.occurrence == 3
    assert state.active_ending == 2
    assert state.position.section == "B"
    assert state.position.active_chord.display() == "G7"


def test_live_chart_adapter_does_not_need_to_execute_form_navigation():
    chart = ChordChart(
        "form:repeat",
        "Repeat",
        (
            ChartMeasure(
                1,
                (ChordChange(Fraction(0), ChordSymbol(10, "7")),),
                section="A",
                repeat_start=True,
            ),
            ChartMeasure(
                2,
                (ChordChange(Fraction(0), ChordSymbol(3, "maj7")),),
                section="A",
                repeat_end=True,
            ),
        ),
    )

    first_pass = live_chart_state(
        chart,
        SharedFormCursorView("core:1", 2, Fraction(0), occurrence=1),
    )
    second_pass = live_chart_state(
        chart,
        SharedFormCursorView("core:2", 2, Fraction(0), occurrence=2),
    )

    assert first_pass.position.active_chord.display() == "Ebmaj7"
    assert second_pass.position.active_chord.display() == "Ebmaj7"
    assert first_pass.occurrence == 1
    assert second_pass.occurrence == 2
