from fractions import Fraction

from music_intelligence.transcribe.chord_chart import NavigationMark
from music_intelligence.transcribe.scorebook_ingestion import (
    ObservedChord,
    ObservedMeasure,
    PageAnnotation,
    ScorebookPageObservation,
    compile_scorebook_observation,
    evidence_summary,
)


def test_compile_scorebook_observation_preserves_only_explicit_evidence():
    obs = ScorebookPageObservation(
        source_book_id="scorebook.real.2",
        song_id="score.real2.alfies_theme",
        title="Alfie's Theme",
        pages=(4,),
        meter_numerator=4,
        meter_denominator=4,
        measures=(
            ObservedMeasure(1, section="A", repeat_start=True),
            ObservedMeasure(2),
        ),
        chords=(
            ObservedChord(1, Fraction(0), 10, "m"),
            ObservedChord(1, Fraction(2), 8, "7"),
            ObservedChord(2, Fraction(0), 6, "maj7"),
        ),
        annotations=(
            PageAnnotation("feel_change", "two feel", 4, .99),
            PageAnnotation("feel_change", "in four", 4, .99),
        ),
        provenance=("vision-reviewed-page",),
    )
    result = compile_scorebook_observation(obs)
    assert result.chart.title == "Alfie's Theme"
    assert len(result.chart.measures) == 2
    assert result.chart.key_fifths is None
    assert evidence_summary(result)["feel_change"] == ("two feel", "in four")


def test_compiler_rejects_chord_outside_meter():
    obs = ScorebookPageObservation(
        source_book_id="scorebook.newreal.1",
        song_id="x",
        title="X",
        pages=(1,),
        meter_numerator=4,
        meter_denominator=4,
        measures=(ObservedMeasure(1),),
        chords=(ObservedChord(1, Fraction(4), 0, "7"),),
    )
    try:
        compile_scorebook_observation(obs)
    except ValueError as exc:
        assert "outside measure" in str(exc)
    else:
        raise AssertionError("expected out-of-measure chord rejection")


def test_page_annotation_must_belong_to_observed_span():
    obs = ScorebookPageObservation(
        source_book_id="scorebook.newreal.2",
        song_id="asa",
        title="Asa",
        pages=(9,10),
        meter_numerator=4,
        meter_denominator=4,
        measures=(ObservedMeasure(1),),
        chords=(ObservedChord(1, Fraction(0), 2, "m7"),),
        annotations=(PageAnnotation("written_bass_part", "dedicated bass page", 11),),
    )
    try:
        obs.validate()
    except ValueError as exc:
        assert "outside observation span" in str(exc)
    else:
        raise AssertionError("expected annotation-page validation error")
