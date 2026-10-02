from music_intelligence.drums.bebop import (
    BebopPhraseMemory,
    SoloistEnergyProjection,
)
from music_intelligence.drums.bebop_runtime import (
    BebopRuntimeProjection,
    build_bebop_candidates,
    score_bebop_gesture,
)
from music_intelligence.drums.model import (
    DrummerRuntimeContext,
    DrummerSoftPlan,
    DrumVoice,
)
from music_intelligence.drums.ride_continuity import RideContinuityMemory
from music_intelligence.drums.timing import tempo_conditioned_swing_prior


def projection(ride_memory=RideContinuityMemory()):
    return BebopRuntimeProjection(
        soloist=SoloistEnergyProjection(0.5, 0.5, 0.0),
        phrase_memory=BebopPhraseMemory(),
        ride_memory=ride_memory,
    )


def test_bebop_runtime_replaces_generic_canonical_time_with_ride_continuity():
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}))
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0, tempo_bpm=140)
    candidates = build_bebop_candidates(plan, ctx, projection())

    time = [g for g in candidates if g.role.value == "time"]
    assert any("ride_continuity" in g.tags for g in time)
    assert not any(
        "timekeeping" in g.tags
        and "ride_continuity" not in g.tags
        and "source_pattern" not in g.tags
        for g in time
    )


def test_skip_in_coast_has_real_omit_candidate():
    prior = tempo_conditioned_swing_prior(140)
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}))
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=1.0 + prior.offbeat_fraction,
        tempo_bpm=140,
        soloist_activity=0.9,
    )
    p = BebopRuntimeProjection(
        soloist=SoloistEnergyProjection(0.9, 0.85, 0.3),
        phrase_memory=BebopPhraseMemory(
            recent_comp_density=0.8,
            recent_response_count=4,
        ),
        ride_memory=RideContinuityMemory(),
    )
    candidates = build_bebop_candidates(plan, ctx, p)
    assert any("omit_skip" in g.tags for g in candidates)


def test_recent_quarter_omission_rewards_reassertion():
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}))
    ctx = DrummerRuntimeContext(position_in_bar_beats=2.0, tempo_bpm=140)
    p = projection(RideContinuityMemory(
        recent_quarter_omissions=1,
        beats_since_clear_quarter=2.0,
    ))
    candidates = build_bebop_candidates(plan, ctx, p)
    reassert = next(g for g in candidates if "reassert_time" in g.tags)
    scored = score_bebop_gesture(reassert, plan, ctx, p)
    assert any(name == "ride_surface_continuity" and value > 0 for name, value in scored.components)


def test_pedal_hihat_anchor_survives_ride_continuity_replacement_on_beat_two():
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}))
    ctx = DrummerRuntimeContext(position_in_bar_beats=1.0, tempo_bpm=140)
    candidates = build_bebop_candidates(plan, ctx, projection())
    ride_time = next(
        g for g in candidates
        if "ride_continuity" in g.tags and any(h.voice is DrumVoice.RIDE for h in g.hits)
    )
    assert any(h.voice is DrumVoice.CLOSED_HIHAT for h in ride_time.hits)
