import pytest

from music_intelligence.research.aligned_performance import (
    DownbeatAnchor,
    LocalBeatTimeMap,
    PerformanceNote,
    ScoreNote,
    align_note_sequences,
    analyze_aligned_performance,
)


def test_local_beat_map_tracks_rubato_measure_by_measure():
    beat_map = LocalBeatTimeMap((
        DownbeatAnchor(0.0, 10.0),
        DownbeatAnchor(4.0, 11.2),
        DownbeatAnchor(8.0, 12.6),
    ))
    assert beat_map.time_at(2.0) == pytest.approx(10.6)
    assert beat_map.time_at(6.0) == pytest.approx(11.9)
    assert beat_map.seconds_per_beat_at(2.0) == pytest.approx(.3)
    assert beat_map.seconds_per_beat_at(6.0) == pytest.approx(.35)


def test_pitch_sequence_alignment_survives_spurious_performance_note():
    score = [ScoreNote(p, i * .5, .5) for i, p in enumerate((60, 62, 64, 65))]
    perf = [
        PerformanceNote(60, 0.0, .1),
        PerformanceNote(61, .1, .2),
        PerformanceNote(62, .2, .3),
        PerformanceNote(64, .4, .5),
        PerformanceNote(65, .6, .7),
    ]
    assert align_note_sequences(score, perf) == ((0, 0), (1, 2), (2, 3), (3, 4))


def test_analysis_recovers_metric_offsets_and_swing_ratio():
    score = [
        ScoreNote(60, 0.0, .5),
        ScoreNote(62, .5, .5),
        ScoreNote(64, 1.0, .5),
        ScoreNote(65, 1.5, .5),
        ScoreNote(67, 2.0, 1.0),
    ]
    beat_map = LocalBeatTimeMap((DownbeatAnchor(0, 0.0), DownbeatAnchor(4, 1.2)))
    perf = [
        PerformanceNote(60, .010, .145),
        PerformanceNote(62, .210, .280),
        PerformanceNote(64, .310, .445),
        PerformanceNote(65, .510, .580),
        PerformanceNote(67, .610, .900),
    ]
    aligned, swings, summary = analyze_aligned_performance(score, perf, beat_map)
    assert summary.matched_notes == 5
    assert summary.match_coverage == pytest.approx(1.0)
    assert summary.metric_offset_ms["beat"] == pytest.approx(10.0)
    assert summary.metric_offset_ms["eighth_upbeat"] == pytest.approx(60.0)
    assert summary.swing_pair_count >= 1
    assert swings[0].ratio == pytest.approx(2.0)


def test_duration_ratio_is_relative_to_local_beat_duration():
    score = [ScoreNote(60, 0.0, 1.0)]
    perf = [PerformanceNote(60, .0, .15)]
    beat_map = LocalBeatTimeMap((DownbeatAnchor(0, 0.0), DownbeatAnchor(4, 1.2)))
    aligned, _, summary = analyze_aligned_performance(score, perf, beat_map)
    assert aligned[0].expected_duration_s == pytest.approx(.3)
    assert aligned[0].duration_ratio == pytest.approx(.5)
    assert summary.mean_duration_ratio == pytest.approx(.5)
