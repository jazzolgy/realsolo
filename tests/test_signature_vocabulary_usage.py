from music_intelligence.legends import (
    SignatureStatus,
    VocabularyDimension,
    VocabularyMemoryItem,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.vocabulary import (
    rank_vocabulary_items,
    score_vocabulary_item,
    vocabulary_use_score,
)


def sig(
    vocabulary_id,
    *,
    status=SignatureStatus.SIGNATURE_CONFIRMED,
    recent=0,
    confidence=.9,
):
    return VocabularyMemoryItem(
        vocabulary_id=vocabulary_id,
        source_id="parker-test",
        source_instrument="sax",
        dimensions=frozenset({
            VocabularyDimension.PITCH_INTERVAL,
            VocabularyDimension.RHYTHM,
            VocabularyDimension.CONTOUR,
        }),
        transferable_to=frozenset({"piano","sax","bass","drums"}),
        candidate_uses=frozenset(VocabularyUseType),
        signature_status=status,
        signature_evidence_count=3 if status is SignatureStatus.SIGNATURE_CONFIRMED else 1,
        recent_usage_count=recent,
        confidence=confidence,
    )


def test_confirmed_signature_requires_repeated_evidence():
    item=VocabularyMemoryItem(
        vocabulary_id="bad",
        source_id="test",
        signature_status=SignatureStatus.SIGNATURE_CONFIRMED,
        signature_evidence_count=1,
    )
    try:
        item.validate()
    except ValueError as exc:
        assert "repeated evidence" in str(exc)
    else:
        raise AssertionError("confirmed signature should require repeated evidence")


def test_literal_quote_has_more_scarcity_than_hybrid():
    item=sig("PARKER-SIG-001",recent=2)
    literal=vocabulary_use_score(
        item,
        VocabularyQuery(
            legend_id="charlie_parker",
            target_instrument="sax",
            preferred_use=VocabularyUseType.LITERAL_QUOTE,
        ),
    )
    hybrid=vocabulary_use_score(
        item,
        VocabularyQuery(
            legend_id="charlie_parker",
            target_instrument="sax",
            preferred_use=VocabularyUseType.HYBRID_COMPOSITION,
        ),
    )
    assert literal.scarcity_penalty > hybrid.scarcity_penalty
    assert hybrid.total > literal.total


def test_confirmed_signature_can_still_be_literal_when_explicitly_requested():
    item=sig("PARKER-SIG-002")
    score=score_vocabulary_item(
        item,
        VocabularyQuery(
            legend_id="charlie_parker",
            target_instrument="piano",
            preferred_use=VocabularyUseType.LITERAL_QUOTE,
        ),
    )
    assert score is not None
    assert score.signature_bias > 0
    assert score.scarcity_penalty > 0


def test_default_retrieval_prefers_transformative_use_for_signature():
    signature=sig("SIG",recent=1,confidence=.9)
    ordinary=VocabularyMemoryItem(
        vocabulary_id="ORD",
        source_id="test",
        source_instrument="sax",
        dimensions=signature.dimensions,
        transferable_to=signature.transferable_to,
        candidate_uses=frozenset(VocabularyUseType),
        confidence=.9,
    )
    ranked=rank_vocabulary_items(
        (ordinary,signature),
        VocabularyQuery(
            legend_id="charlie_parker",
            target_instrument="piano",
            required_dimensions=frozenset({VocabularyDimension.RHYTHM}),
        ),
    )
    assert ranked[0].vocabulary_id=="SIG"


def test_recent_literal_signature_can_fall_below_fresh_material():
    repeated=sig("REPEATED",recent=5,confidence=.93)
    fresh=sig(
        "FRESH",
        status=SignatureStatus.SIGNATURE_CANDIDATE,
        recent=0,
        confidence=.90,
    )
    ranked=rank_vocabulary_items(
        (repeated,fresh),
        VocabularyQuery(
            legend_id="charlie_parker",
            target_instrument="sax",
            preferred_use=VocabularyUseType.LITERAL_QUOTE,
        ),
    )
    assert ranked[0].vocabulary_id=="FRESH"
