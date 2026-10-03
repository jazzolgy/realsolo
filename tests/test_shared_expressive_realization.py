from music_intelligence.reasoning.expressive_realization import (
    DynamicContour,
    ExpressionProfile,
    ExpressiveContext,
    ExpressiveRole,
    realize_expression,
)
from music_intelligence.reasoning.expression_profile_store import ExpressionProfileStore
from music_intelligence.reasoning.solo_grammar import SoloDevelopmentOperation
from realtime.ensemble_app.stage1_quartet import Stage1QuartetRuntime


def test_relative_profile_contour_survives_absolute_context_scaling():
    profile=ExpressionProfile(
        profile_id="p1",
        source_identity="vocab:P123",
        entry_dynamic=.35,
        peak_position=.5,
        peak_dynamic=.8,
        release_dynamic=.45,
        contour=DynamicContour.RISE_FALL,
    )
    early=realize_expression(
        ExpressiveContext(phrase_position=.1,tension=.4,ensemble_density=.3),
        profile=profile,
    )
    peak=realize_expression(
        ExpressiveContext(phrase_position=.5,tension=.4,ensemble_density=.3),
        profile=profile,
    )
    late=realize_expression(
        ExpressiveContext(phrase_position=.9,tension=.4,ensemble_density=.3),
        profile=profile,
    )
    assert peak.dynamic_level > early.dynamic_level
    assert peak.dynamic_level > late.dynamic_level
    assert early.phrase_contour is DynamicContour.RISE_FALL


def test_busy_ensemble_reduces_absolute_level_without_destroying_profile_shape():
    profile=ExpressionProfile(
        profile_id="p2",
        source_identity="vocab:P123",
        entry_dynamic=.45,
        peak_dynamic=.8,
        release_dynamic=.5,
    )
    open_context=realize_expression(
        ExpressiveContext(phrase_position=.55,ensemble_density=.2),
        profile=profile,
    )
    busy_context=realize_expression(
        ExpressiveContext(phrase_position=.55,ensemble_density=.95),
        profile=profile,
    )
    assert busy_context.dynamic_level < open_context.dynamic_level
    assert busy_context.phrase_contour is open_context.phrase_contour


def test_repetition_variation_is_not_monotonic_louder():
    values=[
        realize_expression(
            ExpressiveContext(
                phrase_position=.5,
                repetition_index=i,
                motif_operation=SoloDevelopmentOperation.VARY,
            )
        ).dynamic_level
        for i in range(4)
    ]
    assert values[2] > values[0]
    assert values[3] < values[2]


def test_expression_profile_store_is_separate_from_vocabulary_identity():
    store=ExpressionProfileStore()
    store.add(ExpressionProfile(
        profile_id="soft",
        source_identity="vocab:P123",
        entry_dynamic=.25,
        peak_dynamic=.5,
        release_dynamic=.3,
    ))
    store.add(ExpressionProfile(
        profile_id="strong",
        source_identity="vocab:P123",
        entry_dynamic=.5,
        peak_dynamic=.9,
        release_dynamic=.6,
        confidence=.9,
    ))
    assert len(store.profiles_for("vocab:P123"))==2
    assert store.choose("vocab:P123") is not None


def test_autumn_leaves_sax_emits_shared_expressive_controls():
    quartet=Stage1QuartetRuntime.create(172.0)
    result=quartet.decide(
        "Cm7","F7",
        beat_in_bar=0.0,
        bar_index=0,
        total_bars=32,
        tempo_bpm=172.0,
        section="A",
    )
    sax=next(
        g for g in result.gestures
        if g.source=="player/sax:canonical_immediate"
    )
    voice=sax.voices[0]
    assert "dynamic_level" in voice.expression_controls
    assert "accent_strength" in voice.expression_controls
    assert "foreground_weight" in voice.expression_controls
    decision=next(d for d in result.decisions if d.player_id=="sax")
    assert "shared_expressive_realization" in decision.intent.provenance
