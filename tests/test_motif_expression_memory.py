from music_intelligence.expression import (
    ExpressiveContext,ExpressivePhase,MotifExpressionMemory,
    RelativeExpressionProfile,ExpressionContour,
    expressive_intent_for_motif,observe_committed_motif_expression,
    to_solo_expression_intent,
)


def ctx(**kw):
    base=dict(
        phrase_maturity=.5,tension=.55,ensemble_density=.5,
        current_foreground_weight=.5,target_foreground_weight=.65,
        register_height=.55,expressive_phase=ExpressivePhase.DEVELOP,
    )
    base.update(kw)
    return ExpressiveContext(**base)


def profile():
    return RelativeExpressionProfile(
        "m.rise_fall",ExpressionContour.RISE_FALL,
        entry_relative=-.2,peak_relative=.45,release_relative=-.3,
        accent_bias=.1,body_bias=.1,confidence=.8,
    )


def test_repeated_motif_uses_expression_memory_without_precomposing_notes():
    memory=MotifExpressionMemory()
    first=expressive_intent_for_motif("A",ctx(),memory=memory,profile=profile())
    observe_committed_motif_expression("A",first,memory,context=ctx())
    second=expressive_intent_for_motif("A",ctx(),memory=memory,profile=profile())
    assert memory.repetition_index("A")==1
    assert second!=first


def test_previous_strong_realization_creates_bounded_contrast_pressure():
    memory=MotifExpressionMemory()
    strong=expressive_intent_for_motif("A",ctx(climax_pressure=1.0),profile=profile())
    observe_committed_motif_expression("A",strong,memory)
    repeated=expressive_intent_for_motif("A",ctx(),memory=memory,profile=profile())
    assert repeated.foreground_weight<=ctx().target_foreground_weight+.2


def test_new_shared_how_intent_adapts_to_existing_player_contract():
    intent=expressive_intent_for_motif("A",ctx(),profile=profile())
    legacy=to_solo_expression_intent(intent)
    assert legacy.dynamic_energy==intent.dynamic_level
    assert legacy.accent==intent.accent_strength
    assert legacy.sustain_ratio>0
