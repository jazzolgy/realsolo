from music_intelligence.legends import (
    LegendDomain,
    LegendProfileView,
    VocabularyMemoryItem,
    VocabularyUseType,
)
from music_intelligence.reasoning.legend_style_core import LegendProfile, StyleTendency
from players.drums.legend_adapter import (
    DrumLegendFeature,
    drum_vocabulary_intent,
    legend_gesture_adjustment,
    project_legend_views,
    vocabulary_reuse_bias,
)
from players.drums.model import DrumGesture, DrumHit, DrumVoice, GestureRole, Limb


def legend_view():
    profile = LegendProfile(
        profile_id="drummer.test",
        display_name="Test Drummer",
        instrument_family="drums",
        era_or_school="bebop",
        tendencies=(
            StyleTendency(
                "ride-flex",
                DrumLegendFeature.RIDE_SURFACE_FLEXIBILITY.value,
                context_tags=frozenset({"fast_bebop"}),
                weight=0.7,
                confidence=0.8,
            ),
            StyleTendency(
                "space",
                DrumLegendFeature.SPACE_PREFERENCE.value,
                context_tags=frozenset({"fast_bebop"}),
                weight=0.6,
                confidence=1.0,
            ),
            StyleTendency(
                "motif",
                DrumLegendFeature.MOTIF_DEVELOPMENT.value,
                weight=0.5,
                confidence=1.0,
            ),
        ),
    )
    return LegendProfileView(
        legend_id="test_drummer",
        profile=profile,
        domain_features={
            LegendDomain.RHYTHM_SUBDIVISION: (
                DrumLegendFeature.RIDE_SURFACE_FLEXIBILITY.value,
            ),
            LegendDomain.BREATH_SPACE: (
                DrumLegendFeature.SPACE_PREFERENCE.value,
            ),
            LegendDomain.MOTIF_DEVELOPMENT: (
                DrumLegendFeature.MOTIF_DEVELOPMENT.value,
            ),
        },
    )


def test_projection_is_contextual_and_not_named_drummer_specific():
    projection = project_legend_views(
        ((legend_view(), 1.0),),
        active_tags=("fast_bebop",),
    )
    assert projection.legend_ids == ("test_drummer",)
    assert projection.bias(DrumLegendFeature.RIDE_SURFACE_FLEXIBILITY) > 0
    assert projection.bias(DrumLegendFeature.SPACE_PREFERENCE) > 0
    assert "parker" not in repr(projection).lower()


def test_ride_gesture_ranking_can_change_from_shared_legend_tendency():
    projection = project_legend_views(
        ((legend_view(), 1.0),),
        active_tags=("fast_bebop",),
    )
    ride = DrumGesture(
        hits=(DrumHit(DrumVoice.RIDE, Limb.RIGHT_HAND, 72),),
        role=GestureRole.TIME,
        tags=frozenset({"ride_continuity"}),
    )
    delta, components = legend_gesture_adjustment(ride, projection)
    assert delta > 0
    assert any(name == "legend_ride_surface" for name, _ in components)


def test_vocabulary_adapter_preserves_reference_not_future_sequence():
    item = VocabularyMemoryItem(
        vocabulary_id="DR-LICK-001",
        source_id="recording.example",
        literal_representation="private-shared-material",
        rhythm="triplet-cell",
        articulation="light-ride",
        contour="orchestration-rise",
        quotation_type=VocabularyUseType.ADAPTED_LICK,
        recent_usage_count=1,
        confidence=0.9,
        provenance=("shared_legend",),
    )
    intent = drum_vocabulary_intent(item, use_type=VocabularyUseType.HYBRID_COMPOSITION)
    assert intent.vocabulary_id == "DR-LICK-001"
    assert intent.use_type is VocabularyUseType.HYBRID_COMPOSITION
    assert not hasattr(intent, "future_hits")
    assert not hasattr(intent, "literal_representation")


def test_literal_quote_is_allowed_but_requires_source_material():
    item = VocabularyMemoryItem(
        vocabulary_id="DR-Q-001",
        source_id="recording.example",
        literal_representation="stored-in-shared-memory",
    )
    intent = drum_vocabulary_intent(item, use_type=VocabularyUseType.LITERAL_QUOTE)
    assert intent.use_type is VocabularyUseType.LITERAL_QUOTE


def test_recent_overuse_reduces_vocabulary_reuse_bias():
    base = VocabularyMemoryItem(
        vocabulary_id="DR-FRAG-1",
        source_id="recording.example",
        rhythm="short-cell",
        confidence=1.0,
    )
    fresh = drum_vocabulary_intent(base, use_type=VocabularyUseType.FRAGMENT_RECALL)
    used = drum_vocabulary_intent(
        VocabularyMemoryItem(
            vocabulary_id="DR-FRAG-1",
            source_id="recording.example",
            rhythm="short-cell",
            confidence=1.0,
            recent_usage_count=6,
        ),
        use_type=VocabularyUseType.FRAGMENT_RECALL,
    )
    assert vocabulary_reuse_bias(used) < vocabulary_reuse_bias(fresh)
