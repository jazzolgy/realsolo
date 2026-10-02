from music_intelligence.harmony import HarmonicSpan
from music_intelligence.realsolo_notation_adapter import (
    ChartFormMeasure,
    chord_chart_from_harmonic_spans,
)
from music_intelligence.transcribe import MeasureRepeatKind, NavigationMark


def test_shared_harmony_projects_to_live_chart_without_reinference():
    spans = (
        HarmonicSpan(
            "h1",
            start_beat=0.0,
            duration_beats=2.0,
            root_pc=2,
            symbol="Dm7",
            provenance=("shared:h1",),
        ),
        HarmonicSpan(
            "h2",
            start_beat=2.0,
            duration_beats=2.0,
            root_pc=7,
            symbol="G7alt",
            provenance=("shared:h2",),
        ),
        HarmonicSpan(
            "h3",
            start_beat=4.0,
            duration_beats=4.0,
            root_pc=0,
            symbol="Cmaj7",
            provenance=("shared:h3",),
        ),
    )

    chart = chord_chart_from_harmonic_spans(
        spans,
        chart_id="standard:1",
        title="Standard",
        form_by_measure={
            1: ChartFormMeasure(section="A", repeat_start=True),
            2: ChartFormMeasure(
                section="A",
                repeat_end=True,
                navigation_marks=(NavigationMark.FINE,),
            ),
        },
    )

    assert [c.chord.display() for c in chart.measures[0].chords] == ["Dm7", "G7alt"]
    assert chart.measures[1].chords[0].chord.display() == "Cmaj7"
    assert chart.measures[0].section == "A"
    assert chart.measures[1].navigation_marks == (NavigationMark.FINE,)
    assert "shared:h2" in chart.provenance


def test_repeat_shorthand_is_presentation_form_not_new_harmony():
    spans = (
        HarmonicSpan(
            "h1",
            start_beat=0.0,
            duration_beats=8.0,
            root_pc=0,
            symbol="C7",
        ),
    )

    chart = chord_chart_from_harmonic_spans(
        spans,
        chart_id="repeat:1",
        title="Repeat",
        form_by_measure={
            2: ChartFormMeasure(repeat_shorthand=MeasureRepeatKind.ONE_BAR),
        },
    )

    assert chart.measures[0].chords[0].chord.display() == "C7"
    assert chart.measures[1].chords == ()
    assert chart.measures[1].repeat_shorthand is MeasureRepeatKind.ONE_BAR
