from music_intelligence.drums.bebop import (
    BebopPhraseMemory,
    SoloistEnergyProjection,
    BebopInteractionState,
    BebopCompIntent,
    BassDrumIntent,
)
from music_intelligence.drums.bebop_profile import (
    DEFAULT_BEBOP_PROFILE,
    PriorEvidence,
)
from music_intelligence.drums.bebop_runtime import (
    BebopRuntimeProjection,
    build_bebop_candidates,
    perform_one_bebop_gesture,
    score_bebop_gesture,
)
from music_intelligence.drums.model import (
    DrummerRuntimeContext,
    DrummerSoftPlan,
)
from music_intelligence.drums.online_drummer import DrummerPerformanceMemory


def test_default_bebop_profile_marks_engineering_uncertainty():
    DEFAULT_BEBOP_PROFILE.validate()
    assert PriorEvidence.ENGINEERING_PROVISIONAL in (
        DEFAULT_BEBOP_PROFILE.intentional_non_response.evidence
    )


def test_coast_can_choose_intentional_non_response_over_more_comping():
    plan = DrummerSoftPlan(
        style_tags=frozenset({"jazz", "bop"}),
        energy=0.65,
        comping_density=0.6,
    )
    context = DrummerRuntimeContext(
        position_in_bar_beats=0.5,
        phrase_position=0.5,
        soloist_activity=0.9,
        ensemble_activity=0.7,
    )
    projection = BebopRuntimeProjection(
        SoloistEnergyProjection(
            activity=0.9,
            current_energy=0.85,
            energy_slope=0.35,
        ),
        BebopPhraseMemory(
            recent_comp_density=0.78,
            recent_response_count=4,
        ),
    )
    chosen = perform_one_bebop_gesture(
        plan, context, projection, DrummerPerformanceMemory()
    )
    assert chosen.interaction.state is BebopInteractionState.COAST
    assert chosen.comp_intent is BebopCompIntent.INTENTIONAL_NON_RESPONSE
    assert "intentional_non_response" in chosen.gesture.tags


def test_build_rewards_active_comping_when_there_is_headroom():
    plan = DrummerSoftPlan(
        style_tags=frozenset({"jazz", "bop"}),
        energy=0.55,
        comping_density=0.45,
    )
    context = DrummerRuntimeContext(
        position_in_bar_beats=0.5,
        phrase_position=0.5,
        soloist_activity=0.65,
        ensemble_activity=0.35,
    )
    projection = BebopRuntimeProjection(
        SoloistEnergyProjection(0.65, 0.7, 0.4),
        BebopPhraseMemory(recent_comp_density=0.1),
    )
    scored = [
        score_bebop_gesture(g, plan, context, projection)
        for g in build_bebop_candidates(plan, context, projection)
    ]
    assert any(
        s.interaction.state is BebopInteractionState.BUILD
        and s.comp_intent is BebopCompIntent.STIMULATE
        for s in scored
    )
    assert max(scored, key=lambda s: s.score).comp_intent is BebopCompIntent.STIMULATE


def test_quiet_bass_floor_is_separate_from_interactive_accent():
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}), energy=0.35)
    context = DrummerRuntimeContext(
        position_in_bar_beats=0.0,
        phrase_position=0.4,
        soloist_activity=0.4,
    )
    projection = BebopRuntimeProjection(
        SoloistEnergyProjection(0.4, 0.45, 0.0),
        BebopPhraseMemory(),
    )
    scored = [
        score_bebop_gesture(g, plan, context, projection)
        for g in build_bebop_candidates(plan, context, projection)
    ]
    floor = [s for s in scored if "bass_floor_support" in s.gesture.tags]
    assert floor
    assert all(s.bass_intent is BassDrumIntent.FLOOR_SUPPORT for s in floor)


def test_phrase_pacing_penalizes_more_activity_after_dense_recent_comping():
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}), comping_density=0.6)
    context = DrummerRuntimeContext(position_in_bar_beats=0.5, phrase_position=0.5)
    low_memory = BebopRuntimeProjection(
        SoloistEnergyProjection(0.45, 0.5, 0.0),
        BebopPhraseMemory(recent_comp_density=0.1),
    )
    high_memory = BebopRuntimeProjection(
        SoloistEnergyProjection(0.45, 0.5, 0.0),
        BebopPhraseMemory(recent_comp_density=0.9),
    )
    candidates = build_bebop_candidates(plan, context, low_memory)
    comp = next(g for g in candidates if g.role.value == "comp")

    low = score_bebop_gesture(comp, plan, context, low_memory)
    high = score_bebop_gesture(comp, plan, context, high_memory)
    assert high.score < low.score
