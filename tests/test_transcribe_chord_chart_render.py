from fractions import Fraction

from music_intelligence.transcribe import (
    ChartMeasure,
    ChordChange,
    ChordChart,
    ChordSymbol,
    EnharmonicPolicy,
    MeasureRepeatKind,
    chart_position,
)
from music_intelligence.transcribe.chord_chart_render import (
    build_chord_chart_render_model,
)


def _chart():
    return ChordChart(
        "render:1",
        "Render",
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
            ChartMeasure(
                3,
                (),
                section="A",
                repeat_shorthand=MeasureRepeatKind.ONE_BAR,
            ),
            ChartMeasure(
                4,
                (ChordChange(Fraction(0), ChordSymbol(5, "maj7")),),
                section="B",
            ),
            ChartMeasure(
                5,
                (ChordChange(Fraction(0), ChordSymbol(10, "7")),),
                section="B",
            ),
        ),
    )


def test_render_model_chunks_measures_into_rows():
    model = build_chord_chart_render_model(_chart(), measures_per_row=4)

    assert len(model.rows) == 2
    assert [m.measure_number for m in model.rows[0].measures] == [1, 2, 3, 4]
    assert [m.measure_number for m in model.rows[1].measures] == [5]


def test_render_model_marks_current_measure_and_chord():
    chart = _chart()
    pos = chart_position(chart, measure_number=1, beat=Fraction(3))

    model = build_chord_chart_render_model(
        chart,
        position=pos,
        measures_per_row=4,
        transpose_semitones=2,
    )

    first = model.rows[0].measures[0]
    assert first.is_active_measure is True
    assert [c.is_active for c in first.chords] == [False, True]
    assert model.current_chord_label == "A7"
    assert model.next_chord_label == "Dmaj7"
    assert model.current_section == "A"
    assert model.transpose_semitones == 2


def test_render_model_preserves_repeat_shorthand_while_resolving_visible_chords():
    model = build_chord_chart_render_model(_chart())
    repeated = model.rows[0].measures[2]

    assert repeated.repeat_shorthand is MeasureRepeatKind.ONE_BAR
    assert [c.label for c in repeated.chords] == ["Cmaj7"]


def test_render_transposition_changes_visible_and_preview_labels():
    chart = ChordChart(
        "render:transpose",
        "Transpose",
        (
            ChartMeasure(
                1,
                (
                    ChordChange(Fraction(0), ChordSymbol(0, "7")),
                    ChordChange(Fraction(2), ChordSymbol(5, "m7")),
                ),
            ),
            ChartMeasure(
                2,
                (ChordChange(Fraction(0), ChordSymbol(10, "maj7")),),
            ),
        ),
    )
    pos = chart_position(chart, measure_number=1, beat=Fraction(1))

    model = build_chord_chart_render_model(
        chart,
        position=pos,
        transpose_semitones=1,
        enharmonic_policy=EnharmonicPolicy.PREFER_FLATS,
    )

    assert [c.label for c in model.rows[0].measures[0].chords] == ["Db7", "Gbm7"]
    assert model.current_chord_label == "Db7"
    assert model.next_chord_label == "Gb m7".replace(" ", "")


def test_render_can_respell_without_transposing_pitch():
    chart = ChordChart(
        "render:respell",
        "Respell",
        (
            ChartMeasure(
                1,
                (ChordChange(Fraction(0), ChordSymbol(1, "7", enharmonic_policy=EnharmonicPolicy.PREFER_SHARPS)),),
            ),
        ),
    )

    model = build_chord_chart_render_model(
        chart,
        enharmonic_policy=EnharmonicPolicy.PREFER_FLATS,
    )

    assert model.rows[0].measures[0].chords[0].label == "Db7"
