from music_intelligence.drums.bebop import (
    BebopPhraseMemory,
    SoloistEnergyProjection,
)
from music_intelligence.drums.bebop_runtime import (
    BebopRuntimeProjection,
    build_bebop_candidates,
    score_bebop_gesture,
)
from music_intelligence.drums.comping_phrase import (
    SnareMotifIdentity,
    SnarePhraseMemory,
)
from music_intelligence.drums.model import DrummerRuntimeContext, DrummerSoftPlan


def test_generic_snare_comp_is_replaced_by_phrase_engine():
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}), comping_density=0.8)
    ctx = DrummerRuntimeContext(position_in_bar_beats=1.0, phrase_position=0.4)
    projection = BebopRuntimeProjection(
        soloist=SoloistEnergyProjection(0.4, 0.5, 0.0),
        phrase_memory=BebopPhraseMemory(),
        snare_memory=SnarePhraseMemory(),
    )
    candidates = build_bebop_candidates(plan, ctx, projection)

    assert all("snare_comp" not in g.tags for g in candidates)
    assert any("snare_phrase" in g.tags for g in candidates)


def test_return_after_space_is_scored_as_phrase_development():
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}))
    ctx = DrummerRuntimeContext(position_in_bar_beats=1.0, phrase_position=0.55)
    projection = BebopRuntimeProjection(
        soloist=SoloistEnergyProjection(0.45, 0.5, 0.0),
        phrase_memory=BebopPhraseMemory(),
        snare_memory=SnarePhraseMemory(
            motif=SnareMotifIdentity((0.25,)),
            bars_since_motif_statement=1.5,
            recent_space_bars=1.0,
            consecutive_related_statements=1,
        ),
    )
    candidates = build_bebop_candidates(plan, ctx, projection)
    returned = next(g for g in candidates if "return" in g.tags)
    scored = score_bebop_gesture(returned, plan, ctx, projection)

    assert any(
        name == "snare_phrase_development" and value > 0
        for name, value in scored.components
    )
    assert any(name == "snare_motif_relation" for name, _ in scored.components)


def test_dense_recent_phrase_can_leave_space_instead_of_answering_again():
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}), comping_density=0.7)
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=0.5,
        phrase_position=0.5,
        soloist_activity=0.9,
    )
    projection = BebopRuntimeProjection(
        soloist=SoloistEnergyProjection(0.9, 0.85, 0.35),
        phrase_memory=BebopPhraseMemory(
            recent_comp_density=0.85,
            recent_response_count=4,
        ),
        snare_memory=SnarePhraseMemory(
            motif=SnareMotifIdentity((0.25,)),
            bars_since_motif_statement=0.25,
            consecutive_related_statements=2,
        ),
    )

    candidates = build_bebop_candidates(plan, ctx, projection)
    phrase_space = next(g for g in candidates if "leave_space" in g.tags)
    scored = score_bebop_gesture(phrase_space, plan, ctx, projection)

    assert any(
        name == "snare_phrase_development" and value > 0.5
        for name, value in scored.components
    )
