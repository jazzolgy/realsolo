from fractions import Fraction

from music_intelligence.transcribe import (
    ChartMeasure,
    ChordChange,
    ChordChart,
    ChordSymbol,
    MeasureRepeatKind,
    chart_position,
    resolved_measure_chords,
)


def test_one_bar_repeat_resolves_previous_harmony_for_live_display():
    chart = ChordChart(
        "repeat:one",
        "One Bar Repeat",
        (
            ChartMeasure(
                1,
                (
                    ChordChange(Fraction(0), ChordSymbol(2, "m7")),
                    ChordChange(Fraction(2), ChordSymbol(7, "7")),
                ),
            ),
            ChartMeasure(
                2,
                (),
                repeat_shorthand=MeasureRepeatKind.ONE_BAR,
            ),
            ChartMeasure(
                3,
                (ChordChange(Fraction(0), ChordSymbol(0, "maj7")),),
            ),
        ),
    )

    resolved = resolved_measure_chords(chart, 2)
    position = chart_position(chart, measure_number=2, beat=Fraction(5, 2))

    assert [x.chord.display() for x in resolved] == ["Dm7", "G7"]
    assert position.active_chord.display() == "G7"
    assert position.next_chord.display() == "Cmaj7"


def test_two_bar_repeat_resolves_measure_two_bars_back():
    chart = ChordChart(
        "repeat:two",
        "Two Bar Repeat",
        (
            ChartMeasure(1, (ChordChange(Fraction(0), ChordSymbol(5, "maj7")),)),
            ChartMeasure(2, (ChordChange(Fraction(0), ChordSymbol(10, "7")),)),
            ChartMeasure(3, (), repeat_shorthand=MeasureRepeatKind.TWO_BAR),
            ChartMeasure(4, (), repeat_shorthand=MeasureRepeatKind.TWO_BAR),
        ),
    )

    assert resolved_measure_chords(chart, 3)[0].chord.display() == "Fmaj7"
    assert resolved_measure_chords(chart, 4)[0].chord.display() == "Bb7"
