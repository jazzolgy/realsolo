from fractions import Fraction

from music_intelligence.transcribe import (
    ChartMeasure,
    ChordChange,
    ChordChart,
    ChordSymbol,
    NotationEngine,
)


def test_engine_exposes_live_chord_chart_cursor():
    chart = ChordChart(
        "live:1",
        "Live",
        (
            ChartMeasure(
                1,
                (
                    ChordChange(Fraction(0), ChordSymbol(2, "m7")),
                    ChordChange(Fraction(2), ChordSymbol(7, "7")),
                ),
                section="A",
            ),
            ChartMeasure(
                2,
                (ChordChange(Fraction(0), ChordSymbol(0, "maj7")),),
                section="A",
            ),
        ),
    )
    engine = NotationEngine()

    position = engine.chart_position(
        chart,
        measure_number=1,
        beat=Fraction(5, 2),
    )

    assert position.active_chord.display() == "G7"
    assert position.next_chord.display() == "Cmaj7"
    assert position.section == "A"


def test_engine_can_transpose_chart_without_touching_form():
    chart = ChordChart(
        "live:2",
        "Transpose",
        (
            ChartMeasure(
                1,
                (ChordChange(Fraction(0), ChordSymbol(10, "7")),),
                section="Bridge",
                repeat_start=True,
            ),
        ),
    )

    moved = NotationEngine().transpose_chart(chart, 2)

    assert moved.measures[0].chords[0].chord.display() == "C7"
    assert moved.measures[0].section == "Bridge"
    assert moved.measures[0].repeat_start is True
