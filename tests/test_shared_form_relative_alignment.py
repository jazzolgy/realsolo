from music_intelligence.learning.score_alignment import (
    AlignmentStatus,
    AudioScoreAlignment,
    MusicalScoreCoordinate,
    PerformancePhase,
    ScoreAlignedEvidence,
    comparable_core_form_position,
    research_learning_status,
    same_form_relative_position,
)


def make(song, form_length, form_bar, *, phase=PerformancePhase.SOLO, within=True):
    return ScoreAlignedEvidence(
        evidence_id=f"{song}:{form_bar}",
        alignment=AudioScoreAlignment(
            source_id=f"{song}:recording",
            start_s=float(form_bar),
            end_s=float(form_bar) + 1.0,
            coordinate=MusicalScoreCoordinate(
                song_id=song,
                form_length_bars=form_length,
                form_bar=form_bar,
                chorus_index=2,
                performance_phase=phase,
                within_core_form=within,
            ),
        ),
        feature_schema="form_relative.v1",
    )


def test_form_relative_alignment_works_without_score_page():
    ev = make("israel", 12, 9)
    coord = ev.alignment.coordinate
    assert coord.alignment_status is AlignmentStatus.FORM_ALIGNED
    assert coord.distance_to_form_end == 3
    assert research_learning_status(ev) == "form_relative_comparison"


def test_same_form_position_can_compare_different_recordings():
    a = make("autumn_leaves", 32, 29)
    b = make("autumn_leaves", 32, 29)
    assert same_form_relative_position(a, b, require_same_song=True)


def test_cross_tune_form_comparison_is_possible_when_intentionally_requested():
    a = make("autumn_leaves", 32, 31)
    b = make("nardis", 32, 31)
    assert same_form_relative_position(a, b)
    assert not same_form_relative_position(a, b, require_same_song=True)


def test_non_core_segment_is_not_forced_into_form_grid():
    interlude = make(
        "peri_scope",
        32,
        17,
        phase=PerformancePhase.INTERLUDE,
        within=False,
    )
    assert not comparable_core_form_position(interlude.alignment.coordinate)


def test_arbitrary_form_lengths_are_supported():
    for length, bar in ((10, 10), (12, 9), (26, 24), (40, 37), (56, 55), (64, 61), (80, 79)):
        ev = make("x", length, bar)
        ev.validate()
        assert ev.alignment.coordinate.distance_to_form_end == length - bar
