from players.drums.bebop import BebopPhraseMemory, SoloistEnergyProjection
from players.drums.bebop_runtime import (
    BebopRuntimeProjection,
    build_bebop_candidates,
    score_bebop_gesture,
)
from players.drums.chorus_memory import BebopChorusMemory
from players.drums.model import DrummerRuntimeContext, DrummerSoftPlan, DrumVoice, GestureRole


def projection(**kwargs):
    return BebopRuntimeProjection(
        soloist=SoloistEnergyProjection(0.5, 0.55, 0.0),
        phrase_memory=BebopPhraseMemory(),
        **kwargs,
    )


def test_bebop_runtime_removes_ambiguous_generic_kick_comp():
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}), comping_density=0.8)
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0, phrase_position=0.4)
    candidates = build_bebop_candidates(plan, ctx, projection())
    assert all("bass_drum_comp" not in g.tags for g in candidates)


def test_bebop_kick_is_polarized_between_floor_and_bomb():
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}), energy=0.7)
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=0.0,
        phrase_position=0.95,
        requested_kick=False,
    )
    candidates = build_bebop_candidates(plan, ctx, projection())
    floor = next(g for g in candidates if "bass_floor_support" in g.tags)
    bomb = next(g for g in candidates if "bass_bomb" in g.tags)

    floor_kick = next(h for h in floor.hits if h.voice is DrumVoice.BASS_DRUM)
    bomb_kick = next(h for h in bomb.hits if h.voice is DrumVoice.BASS_DRUM)
    assert floor_kick.velocity <= 48
    assert bomb_kick.velocity >= 72
    assert bomb_kick.velocity - floor_kick.velocity >= 24


def test_chorus_backoff_penalizes_active_comp_and_rewards_space():
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}))
    ctx = DrummerRuntimeContext(position_in_bar_beats=1.0, phrase_position=0.5)
    p = projection(
        chorus_memory=BebopChorusMemory(
            recent_8bar_density=0.85,
            need_to_back_off=True,
        )
    )
    candidates = build_bebop_candidates(plan, ctx, p)
    space = next(g for g in candidates if g.role is GestureRole.SPACE)
    active = next(g for g in candidates if g.role is GestureRole.COMP)
    s = score_bebop_gesture(space, plan, ctx, p)
    a = score_bebop_gesture(active, plan, ctx, p)
    assert any(name == "chorus_back_off_space" for name, _ in s.components)
    assert any(name == "chorus_back_off_activity" for name, _ in a.components)
