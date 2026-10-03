from music_intelligence.learning.score_alignment import (
    AlignmentStatus,
    AudioScoreAlignment,
    MusicalScoreCoordinate,
    PerformancePhase,
    ScoreAlignedEvidence,
    research_learning_status,
    same_musical_position,
)


def ev(eid, start, chorus):
    return ScoreAlignedEvidence(
        evidence_id=eid,
        alignment=AudioScoreAlignment(
            source_id="recording",
            start_s=start,
            end_s=start + 1.0,
            coordinate=MusicalScoreCoordinate(
                song_id="autumn_leaves",
                section="A1",
                bar=5,
                beat=2.0,
                chorus_index=chorus,
                performance_phase=PerformancePhase.SOLO,
            ),
        ),
        feature_schema="ensemble.role.v1",
        features={"density": 0.5},
    )


def test_timestamp_is_not_primary_comparison_coordinate():
    first = ev("a", 12.0, 1)
    later = ev("b", 86.0, 3)
    assert same_musical_position(first, later)
    assert not same_musical_position(first, later, ignore_chorus=False)


def test_alignment_level_controls_research_use():
    unaligned = ScoreAlignedEvidence(
        evidence_id="raw",
        alignment=AudioScoreAlignment(
            source_id="mix",
            start_s=1.0,
            end_s=2.0,
            coordinate=MusicalScoreCoordinate(song_id="nardis"),
        ),
        feature_schema="mir.v1",
    )
    assert unaligned.alignment.coordinate.alignment_status is AlignmentStatus.UNALIGNED
    assert research_learning_status(unaligned) == "navigation_only"


def test_section_bar_and_beat_alignment_are_distinct():
    section = MusicalScoreCoordinate(song_id="x", section="B")
    bar = MusicalScoreCoordinate(song_id="x", section="B", bar=9)
    beat = MusicalScoreCoordinate(song_id="x", section="B", bar=9, beat=3.0)
    assert section.alignment_status is AlignmentStatus.SECTION_ALIGNED
    assert bar.alignment_status is AlignmentStatus.BAR_ALIGNED
    assert beat.alignment_status is AlignmentStatus.BEAT_ALIGNED
