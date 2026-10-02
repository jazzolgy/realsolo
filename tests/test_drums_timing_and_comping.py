import pytest

from music_intelligence.drums import (
    DrummerPerformanceMemory,
    DrummerRuntimeContext,
    DrummerSoftPlan,
    DrumVoice,
    GestureRole,
    comping_propensity,
    perform_one_gesture,
    ride_positions_in_two_beat_cell,
    tempo_conditioned_swing_prior,
)


def test_swing_ratio_flattens_as_tempo_rises():
    slow = tempo_conditioned_swing_prior(80)
    medium = tempo_conditioned_swing_prior(140)
    fast = tempo_conditioned_swing_prior(300)

    assert slow.swing_ratio > medium.swing_ratio > fast.swing_ratio >= 1.0
    assert slow.offbeat_fraction > medium.offbeat_fraction > fast.offbeat_fraction


def test_medium_swing_anchor_is_not_hardcoded_for_all_tempi():
    medium = tempo_conditioned_swing_prior(140)
    fast = tempo_conditioned_swing_prior(300)

    medium_positions = ride_positions_in_two_beat_cell(medium)
    fast_positions = ride_positions_in_two_beat_cell(fast)

    assert medium_positions[2] > fast_positions[2]
    assert medium_positions[:2] == (0.0, 1.0)


def test_humanize_is_bounded_by_tempo_prior():
    plan = DrummerSoftPlan(expressive_timing_offset_ms=40.0)
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0, tempo_bpm=300)
    memory = DrummerPerformanceMemory()

    chosen = perform_one_gesture(plan, ctx, memory)
    ride = next((h for h in chosen.gesture.hits if h.voice is DrumVoice.RIDE), None)

    assert ride is not None
    assert abs(ride.microtiming_ms) <= tempo_conditioned_swing_prior(300).max_humanize_ms


def test_snare_and_bass_drum_comping_are_independent_priors():
    plan = DrummerSoftPlan(energy=0.3, comping_density=0.6)
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=0.5,
        ensemble_activity=0.2,
        soloist_activity=0.4,
    )

    prop = comping_propensity(plan, ctx)

    assert prop.snare != prop.bass_drum
    assert 0.0 <= prop.snare <= 1.0
    assert 0.0 <= prop.bass_drum <= 1.0


def test_dense_ensemble_increases_space_propensity():
    plan = DrummerSoftPlan(comping_density=0.25)
    sparse = comping_propensity(
        plan,
        DrummerRuntimeContext(position_in_bar_beats=0.5, ensemble_activity=0.1, soloist_activity=0.2),
    )
    dense = comping_propensity(
        plan,
        DrummerRuntimeContext(position_in_bar_beats=0.5, ensemble_activity=0.95, soloist_activity=0.9),
    )

    assert dense.space > sparse.space
