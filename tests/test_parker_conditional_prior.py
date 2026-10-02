from music_intelligence.legends.parker.conditional_prior import (
    PARKER_SYMBOLIC_MOTION_PROFILE,
    build_statistics,
)
from music_intelligence.legends.parker.mixture import PARKER_V131_BLEND
from music_intelligence.reasoning.legend_style_core import (
    CandidateEvent,
    LegendBlend,
    MusicalContextVector,
)
from music_intelligence.reasoning.online_improviser import OnlineMusicalEvaluator


def test_conditional_statistics_regression():
    s = build_statistics()
    assert s.corpus_licks == 131
    assert 0.60 < s.global_motion.step_share < 0.63
    assert 0.94 < s.global_motion.within_p4_share < 0.96
    assert 0.03 < s.global_motion.wide_leap_share < 0.06
    assert s.global_motion.compound_leap_share == 0.0


def test_wide_leap_recovery_is_compact_and_contrary():
    s = build_statistics()
    assert s.wide_leap_count_with_followup >= 50
    assert s.wide_leap_contrary_recovery_share > 0.80
    assert s.wide_leap_next_within_p4_share > 0.95


def test_short_window_compound_span_is_exceptional():
    s = build_statistics()
    assert s.three_note_span_gt_octave_share < 0.002
    assert s.four_note_span_gt_octave_share < 0.01


def test_statistical_profile_is_policy_bias_not_note_sequence():
    p = PARKER_SYMBOLIC_MOTION_PROFILE
    assert p.source_count == 131
    assert not hasattr(p, "exact_future_notes")
    b = LegendBlend(((p, 1.0),))
    assert b.feature_bias("contrary_recovery", ("after_wide_leap",)) > 0
    assert b.feature_bias("wide_leap", ()) < 0


def test_evaluator_derives_motion_features_only_at_commit_time():
    ev = OnlineMusicalEvaluator(PARKER_V131_BLEND)
    ctx = MusicalContextVector(
        phrase_maturity=.5,
        previous_pitch_midi=60,
        previous_interval_semitones=9,
        recent_pitches=(51, 60),
    )
    recovered = ev.evaluate(CandidateEvent(58, .5), ctx)
    repeated = ev.evaluate(CandidateEvent(69, .5), ctx)
    assert recovered.total > repeated.total
    assert "legend:contrary_recovery" in recovered.components
    assert "legend:recovery_within_p4" in recovered.components


def test_late_structural_long_tone_receives_bounded_positive_prior():
    ev = OnlineMusicalEvaluator(PARKER_V131_BLEND)
    late = ev.evaluate(CandidateEvent(67, 1.5), MusicalContextVector(phrase_maturity=.85))
    assert late.components["legend:structural_terminal_long_tone"] > 0
