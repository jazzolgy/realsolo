from music_intelligence.expression import (
    ExpressiveContext,ExpressivePhase,ExpressionContour,
    RelativeExpressionProfile,realize_expressive_intent,
)
from music_intelligence.learning import MusicalScoreCoordinate,PerformancePhase


def profile():
    return RelativeExpressionProfile(
        profile_id="bill_evans.test",
        contour=ExpressionContour.RISE_FALL,
        entry_relative=-.2,
        peak_relative=.5,
        release_relative=-.35,
        accent_bias=.15,
        body_bias=.20,
        foreground_bias=.10,
        confidence=.8,
        provenance=("research:test",),
    )


def context(**kw):
    base=dict(
        position=MusicalScoreCoordinate(
            song_id="autumn_leaves",section="B",bar=21,beat=3,
            form_length_bars=32,form_bar=21,chorus_index=2,
            performance_phase=PerformancePhase.SOLO,
        ),
        phrase_maturity=.6,tension=.6,ensemble_density=.5,
        current_foreground_weight=.5,target_foreground_weight=.7,
        register_height=.65,
    )
    base.update(kw)
    return ExpressiveContext(**base)


def test_relative_profile_is_scaled_by_context_not_copied_as_absolute_velocity():
    peak=realize_expressive_intent(context(expressive_phase=ExpressivePhase.PEAK),profile=profile())
    crowded=realize_expressive_intent(
        context(expressive_phase=ExpressivePhase.PEAK,ensemble_density=.95),
        profile=profile(),
    )
    assert peak.dynamic_level>crowded.dynamic_level
    assert peak.contour is ExpressionContour.RISE_FALL


def test_dynamic_and_accent_are_independent_targets():
    release=realize_expressive_intent(
        context(expressive_phase=ExpressivePhase.RELEASE,release_pressure=.9),
        profile=profile(),
    )
    assert release.note_body>release.accent_strength
    assert "cadential_release" in release.articulation_tags


def test_repetition_variation_does_not_force_monotonic_crescendo():
    first=realize_expressive_intent(context(repetition_index=1),profile=profile())
    second=realize_expressive_intent(context(repetition_index=2),profile=profile())
    assert second.dynamic_level<first.dynamic_level
