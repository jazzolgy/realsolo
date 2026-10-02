from music_intelligence.bass.performance_grammar import (
    BassGrammarContext,
    MetricRole,
    MotionStrategy,
    RegisterIntent,
    TargetStrategy,
    evaluate_bass_grammar,
    metric_role,
)


def test_last_walking_beat_is_preparation_role():
    ctx = BassGrammarContext(beat_in_measure=3.0, meter_numerator=4)
    assert metric_role(ctx) is MetricRole.PREPARATION


def test_approach_is_rewarded_on_preparation_beat():
    ctx = BassGrammarContext(beat_in_measure=3.0, meter_numerator=4, previous_pitch_midi=38)
    approach = evaluate_bass_grammar(
        ctx=ctx,
        candidate_pitch_midi=42,
        motion_strategy=MotionStrategy.CHROMATIC_APPROACH,
        target_strategy=TargetStrategy.NEXT_ROOT,
    )
    plain_root = evaluate_bass_grammar(
        ctx=ctx,
        candidate_pitch_midi=38,
        motion_strategy=MotionStrategy.CHORDAL,
        target_strategy=TargetStrategy.CURRENT_ROOT,
    )
    assert approach.score_delta > plain_root.score_delta


def test_beat_one_rewards_root_anchor():
    ctx = BassGrammarContext(beat_in_measure=0.0)
    root = evaluate_bass_grammar(
        ctx=ctx,
        candidate_pitch_midi=36,
        motion_strategy=MotionStrategy.CHORDAL,
        target_strategy=TargetStrategy.CURRENT_ROOT,
    )
    chromatic = evaluate_bass_grammar(
        ctx=ctx,
        candidate_pitch_midi=37,
        motion_strategy=MotionStrategy.CHROMATIC_APPROACH,
        target_strategy=TargetStrategy.NEXT_ROOT,
    )
    assert root.score_delta > chromatic.score_delta


def test_repeated_note_pressure_is_soft_not_prohibition():
    loose = evaluate_bass_grammar(
        ctx=BassGrammarContext(
            beat_in_measure=1.0,
            previous_pitch_midi=40,
            repeated_note_tolerance=1.0,
        ),
        candidate_pitch_midi=40,
        motion_strategy=MotionStrategy.CHORDAL,
        target_strategy=TargetStrategy.CURRENT_CHORD_MEMBER,
    )
    strict = evaluate_bass_grammar(
        ctx=BassGrammarContext(
            beat_in_measure=1.0,
            previous_pitch_midi=40,
            repeated_note_tolerance=0.0,
        ),
        candidate_pitch_midi=40,
        motion_strategy=MotionStrategy.CHORDAL,
        target_strategy=TargetStrategy.CURRENT_CHORD_MEMBER,
    )
    assert loose.score_delta > strict.score_delta


def test_register_intent_is_directional_preference_not_fixed_line():
    up = evaluate_bass_grammar(
        ctx=BassGrammarContext(
            beat_in_measure=1.0,
            previous_pitch_midi=40,
            register_intent=RegisterIntent.ASCEND,
        ),
        candidate_pitch_midi=43,
        motion_strategy=MotionStrategy.CHORDAL,
        target_strategy=TargetStrategy.CURRENT_CHORD_MEMBER,
    )
    down = evaluate_bass_grammar(
        ctx=BassGrammarContext(
            beat_in_measure=1.0,
            previous_pitch_midi=40,
            register_intent=RegisterIntent.ASCEND,
        ),
        candidate_pitch_midi=36,
        motion_strategy=MotionStrategy.CHORDAL,
        target_strategy=TargetStrategy.CURRENT_CHORD_MEMBER,
    )
    assert up.score_delta > down.score_delta
