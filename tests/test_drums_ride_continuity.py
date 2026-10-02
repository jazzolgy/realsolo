from music_intelligence.drums.bebop import BebopInteractionState
from music_intelligence.drums.bebop_profile import DEFAULT_BEBOP_PROFILE
from music_intelligence.drums.model import DrummerRuntimeContext, DrummerSoftPlan
from music_intelligence.drums.ride_continuity import (
    RideContinuityMemory,
    RidePhase,
    RideSurfaceAction,
    build_ride_candidates,
    classify_ride_phase,
    update_ride_memory,
)
from music_intelligence.drums.timing import tempo_conditioned_swing_prior


def test_current_instant_is_classified_as_quarter_or_tempo_conditioned_skip():
    quarter = DrummerRuntimeContext(position_in_bar_beats=1.0, tempo_bpm=140)
    prior = tempo_conditioned_swing_prior(140)
    skip = DrummerRuntimeContext(
        position_in_bar_beats=1.0 + prior.offbeat_fraction,
        tempo_bpm=140,
    )
    assert classify_ride_phase(quarter) is RidePhase.QUARTER
    assert classify_ride_phase(skip) is RidePhase.SKIP


def test_skip_note_can_be_omitted_without_omitting_deep_quarter_pulse():
    prior = tempo_conditioned_swing_prior(140)
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=1.0 + prior.offbeat_fraction,
        tempo_bpm=140,
    )
    candidates = build_ride_candidates(
        DrummerSoftPlan(),
        ctx,
        BebopInteractionState.COAST,
        RideContinuityMemory(),
    )
    actions = {c.action for c in candidates}
    assert RideSurfaceAction.LIFT_SKIP in actions
    assert RideSurfaceAction.OMIT_SKIP in actions


def test_quarter_omission_is_more_costly_than_skip_omission():
    plan = DrummerSoftPlan()
    qctx = DrummerRuntimeContext(position_in_bar_beats=1.0, tempo_bpm=140)
    prior = tempo_conditioned_swing_prior(140)
    sctx = DrummerRuntimeContext(
        position_in_bar_beats=1.0 + prior.offbeat_fraction,
        tempo_bpm=140,
    )
    q = build_ride_candidates(
        plan, qctx, BebopInteractionState.COAST, RideContinuityMemory()
    )
    s = build_ride_candidates(
        plan, sctx, BebopInteractionState.COAST, RideContinuityMemory()
    )
    q_omit = next(c for c in q if c.action is RideSurfaceAction.RELAX_SURFACE)
    s_omit = next(c for c in s if c.action is RideSurfaceAction.OMIT_SKIP)
    assert q_omit.score_bias < s_omit.score_bias


def test_recent_quarter_omission_creates_reassert_time_candidate():
    ctx = DrummerRuntimeContext(position_in_bar_beats=2.0, tempo_bpm=140)
    memory = RideContinuityMemory(
        recent_quarter_omissions=1,
        beats_since_clear_quarter=2.0,
    )
    candidates = build_ride_candidates(
        DrummerSoftPlan(),
        ctx,
        BebopInteractionState.SUPPORT,
        memory,
    )
    assert any(c.action is RideSurfaceAction.REASSERT_TIME for c in candidates)


def test_ride_memory_tracks_surface_history_without_future_pattern():
    memory = RideContinuityMemory()
    memory = update_ride_memory(memory, RideSurfaceAction.HOLD_QUARTER, RidePhase.QUARTER)
    memory = update_ride_memory(memory, RideSurfaceAction.OMIT_SKIP, RidePhase.SKIP)
    assert memory.recent_quarter_hits == 1
    assert memory.recent_skip_omissions == 1
    assert not hasattr(memory, "future_ride_pattern")
