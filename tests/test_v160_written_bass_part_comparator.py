from players.bass.written_part_comparator import (
    BassLineObservation,
    analyze_bass_line,
    compare_bass_lines,
    written_part_prior_from_profile,
)


def obs(p, beat, root, pcs):
    return BassLineObservation(p, beat, root, frozenset(pcs))


def test_comparator_uses_abstract_motion_not_exact_note_identity():
    reference = (
        obs(36,0,0,{0,3,7,10}),
        obs(38,1,0,{0,3,7,10}),
        obs(39,2,0,{0,3,7,10}),
        obs(41,3,5,{5,9,0,3}),
    )
    generated = (
        obs(48,0,0,{0,3,7,10}),
        obs(50,1,0,{0,3,7,10}),
        obs(51,2,0,{0,3,7,10}),
        obs(53,3,5,{5,9,0,3}),
    )
    cmp = compare_bass_lines(reference, generated)
    # Same contour/function an octave apart should remain structurally close.
    assert cmp.feature_distance < .15


def test_profile_detects_scalar_motion_and_register_trajectory():
    events = (
        obs(36,0,0,{0,3,7,10}),
        obs(38,1,0,{0,3,7,10}),
        obs(40,2,0,{0,3,7,10}),
        obs(41,3,5,{5,9,0,3}),
    )
    profile = analyze_bass_line(events)
    assert profile.scalar_motion_rate == 1.0
    assert profile.register_slope > 0
    assert profile.register_span == 5


def test_written_profile_becomes_bounded_prior():
    events = (
        obs(36,0,0,{0,3,7,10}),
        obs(37,1,0,{0,3,7,10}),
        obs(38,2,2,{2,5,9,0}),
    )
    prior = written_part_prior_from_profile(analyze_bass_line(events))
    assert 0.0 <= prior.root_preference <= 1.0
    assert 0.0 <= prior.scalar_preference <= 1.0
    assert 0.0 <= prior.chromatic_preference <= 1.0
