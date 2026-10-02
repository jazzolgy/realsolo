import pytest

from music_intelligence.drums import (
    DrumGesture,
    DrummerPerformanceMemory,
    DrummerRuntimeContext,
    DrummerSoftPlan,
    GestureRole,
    TimeFeel,
    build_immediate_candidates,
    perform_one_gesture,
)
from music_intelligence.harmony import HarmonicFrame


def test_soft_plan_cannot_freeze_future_drum_sequence():
    plan = DrummerSoftPlan(
        exact_future_gestures=(DrumGesture(role=GestureRole.SPACE),),
    )
    with pytest.raises(ValueError, match="freeze future drum gestures"):
        plan.validate()


def test_swing_policy_emits_only_current_gesture_candidates():
    plan = DrummerSoftPlan(feel=TimeFeel.SWING)
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0)
    candidates = build_immediate_candidates(plan, ctx)

    assert candidates
    assert all(isinstance(x, DrumGesture) for x in candidates)
    # No candidate stores a future sequence; every hit is an immediate local hit.
    assert all(abs(hit.microtiming_ms) <= 80 for g in candidates for hit in g.hits)


def test_explicit_ensemble_kick_wins_immediate_decision():
    plan = DrummerSoftPlan(energy=0.7, comping_density=0.3)
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=0.0,
        requested_kick=True,
        ensemble_activity=0.8,
        soloist_activity=0.8,
    )
    memory = DrummerPerformanceMemory()

    chosen = perform_one_gesture(plan, ctx, memory)

    assert chosen.gesture.role is GestureRole.ACCENT
    assert "explicit_cue" in chosen.gesture.tags
    assert memory.committed == [chosen.gesture]


def test_phrase_boundary_can_promote_setup_without_reimplementing_harmony():
    plan = DrummerSoftPlan(energy=0.8, comping_density=0.55)
    harmony = HarmonicFrame(tension=0.9, phrase_position=0.95, cadence_state="approaching")
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=3.0,
        phrase_position=0.95,
        ensemble_activity=0.35,
        energy_target=0.8,
        section_transition=True,
        harmonic_transition_confidence=0.9,
        harmony=harmony,
    )
    memory = DrummerPerformanceMemory()

    chosen = perform_one_gesture(plan, ctx, memory)

    assert chosen.gesture.role is GestureRole.SETUP
    assert any(name == "shared_tension_projection" for name, _ in chosen.components)


def test_high_ensemble_density_rewards_space_candidate():
    plan = DrummerSoftPlan(energy=0.25, comping_density=0.05)
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=0.5,  # swing-grid slot with no ride hit
        ensemble_activity=1.0,
        soloist_activity=1.0,
        energy_target=0.2,
    )
    memory = DrummerPerformanceMemory()

    chosen = perform_one_gesture(plan, ctx, memory)

    assert chosen.gesture.role is GestureRole.SPACE
