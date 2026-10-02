from fractions import Fraction

from music_intelligence.transcribe.chord_chart import (
    BarlineStyle,
    ChartMeasure,
    ChordChange,
    ChordChart,
    ChordSymbol,
    NavigationMark,
    chart_position,
)


def test_live_chart_position_resolves_current_and_next_chord():
    chart = ChordChart(
        "autumn",
        "Autumn",
        (
            ChartMeasure(
                1,
                (
                    ChordChange(Fraction(0), ChordSymbol(0, "maj7")),
                    ChordChange(Fraction(2), ChordSymbol(9, "7")),
                ),
                section="A",
            ),
            ChartMeasure(
                2,
                (ChordChange(Fraction(0), ChordSymbol(2, "m7")),),
                repeat_end=True,
            ),
        ),
    )

    position = chart_position(chart, measure_number=1, beat=Fraction(1))

    assert position.section == "A"
    assert position.active_chord.display() == "Cmaj7"
    assert position.next_chord.display() == "A7"


def test_chart_position_carries_previous_chord_when_measure_starts_empty():
    chart = ChordChart(
        "hold",
        "Hold",
        (
            ChartMeasure(1, (ChordChange(Fraction(0), ChordSymbol(7, "7")),)),
            ChartMeasure(2, ()),
        ),
    )

    position = chart_position(chart, measure_number=2, beat=Fraction(1))

    assert position.active_chord.display() == "G7"
    assert position.next_chord is None


def test_transpose_preserves_form_semantics():
    chart = ChordChart(
        "form",
        "Form",
        (
            ChartMeasure(
                1,
                (ChordChange(Fraction(0), ChordSymbol(10, "maj7")),),
                section="B",
                rehearsal_mark="B",
                repeat_start=True,
                ending_numbers=(1,),
                navigation_marks=(NavigationMark.SEGNO,),
                barline=BarlineStyle.DOUBLE,
            ),
        ),
    )

    moved = chart.transpose(2)
    measure = moved.measures[0]

    assert measure.chords[0].chord.display() == "Cmaj7"
    assert measure.section == "B"
    assert measure.repeat_start is True
    assert measure.ending_numbers == (1,)
    assert measure.navigation_marks == (NavigationMark.SEGNO,)
    assert measure.barline is BarlineStyle.DOUBLE


def test_no_chord_survives_transposition():
    chart = ChordChart(
        "nc",
        "No Chord",
        (
            ChartMeasure(
                1,
                (ChordChange(Fraction(0), ChordSymbol(None, no_chord=True)),),
            ),
        ),
    )

    assert chart.transpose(5).measures[0].chords[0].chord.display() == "N.C."
