from music_intelligence.legends import (
    LegendDomain,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.legends.scott_lafaro import SCOTT_LAFARO_VOCABULARY_INDEX
from music_intelligence.reasoning.motif import (
    MotifSourceType,
    motif_candidate_from_vocabulary,
)


def test_lafaro_vocabulary_becomes_abstract_shared_motif_without_literal_notes():
    items = SCOTT_LAFARO_VOCABULARY_INDEX.query(VocabularyQuery(
        legend_id="scott_lafaro",
        domain=LegendDomain.MOTIF_DEVELOPMENT,
        context_tags=frozenset({"solo", "develop"}),
        target_instrument="bass",
        allowed_uses=frozenset({
            VocabularyUseType.ABSTRACTED_PATTERN,
            VocabularyUseType.HYBRID_COMPOSITION,
        }),
        limit=4,
    ))
    assert items

    candidate = motif_candidate_from_vocabulary(items[0])
    assert candidate.source_type is MotifSourceType.VOCABULARY_SEEDED
    assert candidate.identity.motif_id.startswith("vocabulary:lafaro.")
    assert candidate.identity.interval_schema == ()
    assert candidate.identity.rhythm_schema == ()
    assert candidate.identity.contour
    assert "derived_abstract_no_literal_notes" in candidate.identity.provenance


def test_verified_structured_seeds_can_enrich_vocabulary_motif_without_reconstruction():
    item = SCOTT_LAFARO_VOCABULARY_INDEX.items[0]
    candidate = motif_candidate_from_vocabulary(
        item,
        interval_seed=(3, -2),
        rhythm_seed=(.5, .5, 1.0),
    )
    assert candidate.identity.interval_schema == (3, -2)
    assert candidate.identity.rhythm_schema == (.5, .5, 1.0)
