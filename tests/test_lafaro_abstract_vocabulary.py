from music_intelligence.legends import (
    LegendDomain,
    VocabularyDimension,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.legends.scott_lafaro import SCOTT_LAFARO_VOCABULARY_INDEX


def test_lafaro_alice_abstract_vocabulary_loads_without_literal_notes():
    items = SCOTT_LAFARO_VOCABULARY_INDEX.items
    assert len(items) >= 4
    assert all(item.source_instrument == "bass" for item in items)
    assert all(not item.literal_representation for item in items)
    assert all(not item.transposition_normalized_representation for item in items)


def test_lafaro_rhythmic_vocabulary_is_retrievable_for_bass_solo():
    result = SCOTT_LAFARO_VOCABULARY_INDEX.query(VocabularyQuery(
        legend_id="scott_lafaro",
        domain=LegendDomain.RHYTHM_SUBDIVISION,
        context_tags=frozenset({"solo", "develop"}),
        required_dimensions=frozenset({VocabularyDimension.RHYTHM}),
        target_instrument="bass",
        preferred_use=VocabularyUseType.ABSTRACTED_PATTERN,
        allowed_uses=frozenset({
            VocabularyUseType.ABSTRACTED_PATTERN,
            VocabularyUseType.HYBRID_COMPOSITION,
        }),
        limit=8,
    ))
    assert result
    assert any("polyrhythm" in x.rhythm or "recurrent" in x.rhythm for x in result)


def test_lafaro_interaction_vocabulary_requires_matching_context():
    result = SCOTT_LAFARO_VOCABULARY_INDEX.query(VocabularyQuery(
        legend_id="scott_lafaro",
        domain=LegendDomain.ENSEMBLE_INTERACTION,
        context_tags=frozenset({"solo", "answer", "ensemble_space"}),
        target_instrument="bass",
        allowed_uses=frozenset({VocabularyUseType.ABSTRACTED_PATTERN}),
        limit=4,
    ))
    assert result
    assert result[0].entrance == "respond_to_open_space"
