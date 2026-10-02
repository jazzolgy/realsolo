from players.drums.bebop import BebopInteractionState
from players.drums.model import DrummerRuntimeContext, DrummerSoftPlan
from players.drums.ride_continuity import (
    RideContinuityMemory,
    RidePhase,
    RideSurfaceAction,
    build_ride_candidates,
    classify_ride_phase,
)
from players.drums.timing import tempo_conditioned_swing_prior


def test_skip_surface_never_offers_accent_skip():
    plan = DrummerSoftPlan()
    tempo = 180.0
    prior = tempo_conditioned_swing_prior(tempo)
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=prior.offbeat_fraction,
        tempo_bpm=tempo,
    )
    assert classify_ride_phase(ctx) is RidePhase.SKIP
    candidates = build_ride_candidates(
        plan,
        ctx,
        BebopInteractionState.BUILD,
        RideContinuityMemory(),
    )
    assert all(c.action is not getattr(RideSurfaceAction, "ACCENT_SKIP", None) for c in candidates)
    assert all("accent_skip" not in c.gesture.tags for c in candidates)


def test_listen_makes_skip_omission_more_attractive_than_build():
    plan = DrummerSoftPlan()
    tempo = 180.0
    prior = tempo_conditioned_swing_prior(tempo)
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=prior.offbeat_fraction,
        tempo_bpm=tempo,
    )
    build = build_ride_candidates(
        plan, ctx, BebopInteractionState.BUILD, RideContinuityMemory()
    )
    listen = build_ride_candidates(
        plan, ctx, BebopInteractionState.LISTEN, RideContinuityMemory()
    )
    b = next(c.score_bias for c in build if c.action is RideSurfaceAction.OMIT_SKIP)
    l = next(c.score_bias for c in listen if c.action is RideSurfaceAction.OMIT_SKIP)
    assert l > b
