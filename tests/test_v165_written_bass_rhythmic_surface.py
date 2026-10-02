from players.bass.written_part_comparator import (
    BassLineObservation,
    analyze_bass_line,
)


def test_written_part_profile_measures_sparse_subdivision_over_quarter_floor():
    events = (
        BassLineObservation(36, 0.0, 0, frozenset({0,3,7,10}), 1.0),
        BassLineObservation(38, 1.0, 0, frozenset({0,3,7,10}), .5),
        BassLineObservation(39, 1.5, 0, frozenset({0,3,7,10}), .5),
        BassLineObservation(41, 2.0, 5, frozenset({5,9,0,3}), 1.0),
        BassLineObservation(40, 3.0, 5, frozenset({5,9,0,3}), 1.0),
    )
    profile = analyze_bass_line(events)
    assert profile.offbeat_onset_rate > 0
    assert profile.short_subdivision_rate > 0
    assert profile.quarter_floor_coverage == 1.0
