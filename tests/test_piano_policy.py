from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from music_intelligence.reasoning.online_improviser import SoftPlan
from players.piano import (
    PianoPerformanceState,
    PianoPolicyEvaluator,
    PianoVoicingCandidate,
    perform_one_piano_action,
)


def test_piano_runtime_commits_only_one_action():
    state = PianoPerformanceState()
    plan = SoftPlan(
        4,
        "support soloist",
        soft_targets=("clarity",),
        candidate_families=("shell", "rootless"),
    )
    candidates = [
        PianoVoicingCandidate((52, 59, 62), 0.5, tags=frozenset({"shell"})),
        PianoVoicingCandidate((55, 60, 64, 69), 0.5, tags=frozenset({"dense"})),
    ]

    perform_one_piano_action(
        plan,
        PianoPolicyEvaluator(),
        candidates,
        MusicalContextVector(),
        state,
    )

    assert len(state.committed) == 1


def test_smooth_voice_leading_is_preferred_when_other_factors_match():
    state = PianoPerformanceState(last_voicing=(52, 59, 62))
    evaluator = PianoPolicyEvaluator()
    context = MusicalContextVector()

    smooth = PianoVoicingCandidate((53, 59, 62), 1.0)
    leap = PianoVoicingCandidate((72, 79, 84), 1.0)

    assert evaluator.evaluate(smooth, context, state).total > evaluator.evaluate(
        leap, context, state
    ).total


def test_busy_ensemble_rewards_space_and_penalizes_dense_fill():
    state = PianoPerformanceState()
    evaluator = PianoPolicyEvaluator()
    context = MusicalContextVector(ensemble_activity=0.9)

    space = PianoVoicingCandidate((52, 59), 0.5, tags=frozenset({"leave_space"}))
    fill = PianoVoicingCandidate(
        (48, 55, 59, 62, 65), 0.5, tags=frozenset({"dense", "rhythmic_fill"})
    )

    assert evaluator.evaluate(space, context, state).total > evaluator.evaluate(
        fill, context, state
    ).total


def test_tension_color_is_contextual_not_globally_preferred():
    state = PianoPerformanceState()
    evaluator = PianoPolicyEvaluator()
    color = PianoVoicingCandidate(
        (52, 58, 63, 68), 0.5, tags=frozenset({"upper_structure"})
    )

    high = evaluator.evaluate(color, MusicalContextVector(tension=0.85), state)
    low = evaluator.evaluate(color, MusicalContextVector(tension=0.2), state)

    assert high.total > low.total
