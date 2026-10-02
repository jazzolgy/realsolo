from music_intelligence.legends import (
    LegendDomain,
    LegendQueryContext,
    VocabularyCandidateFamily,
    VocabularyIndex,
    VocabularyQuery,
)
from music_intelligence.legends.parker import (
    PARKER_PROFILE_VIEW,
    parker_vocabulary_item,
)


def test_six_vocabulary_candidate_families_are_explicit():
    assert {x.value for x in VocabularyCandidateFamily} == {
        "literal_quote",
        "transposed_lick",
        "adapted_lick",
        "fragment_recall",
        "abstracted_pattern",
        "hybrid_composition",
    }


def test_parker_profile_view_queries_by_domain_and_context():
    matches = PARKER_PROFILE_VIEW.query(
        LegendDomain.INTERVAL_LEAP_GRAMMAR,
        LegendQueryContext(active_tags=frozenset({"after_wide_leap"})),
    )
    assert any(x.feature == "contrary_recovery" for x in matches)
    assert all(x.profile_id.startswith("legend.charlie_parker") for x in matches)


def test_uncovered_domain_does_not_invent_evidence():
    assert PARKER_PROFILE_VIEW.query(LegendDomain.MOTIF_DEVELOPMENT) == ()


def test_vocabulary_index_accepts_literal_and_hybrid_memory():
    item = parker_vocabulary_item(
        vocabulary_id="CP-TEST-001",
        source_id="test-source",
        kind="lick",
        candidate_families=frozenset({
            VocabularyCandidateFamily.LITERAL_QUOTE,
            VocabularyCandidateFamily.HYBRID_COMPOSITION,
        }),
        harmonic_function="dominant",
        phrase_position="late",
        context_tags=frozenset({"answer"}),
        literal_representation_hash="abc",
        normalized_pitch_rhythm_hash="def",
        confidence=.9,
    )
    index = VocabularyIndex((item,))
    matches = index.query(VocabularyQuery(
        legend_id="charlie_parker",
        harmonic_function="dominant",
        phrase_position="late",
        required_tags=frozenset({"answer"}),
    ))
    assert matches and matches[0].item.vocabulary_id == "CP-TEST-001"


def test_vocabulary_schema_does_not_contain_frozen_future_solo_field():
    item = parker_vocabulary_item(
        vocabulary_id="CP-TEST-002",
        source_id="test-source",
        kind="fragment",
        candidate_families=frozenset({VocabularyCandidateFamily.FRAGMENT_RECALL}),
    )
    assert not hasattr(item, "future_phrase")
    assert not hasattr(item, "exact_future_notes")
