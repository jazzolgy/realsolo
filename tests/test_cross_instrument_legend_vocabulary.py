from music_intelligence.legends import (
    VocabularyDimension,
    VocabularyMemoryItem,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.legends.bill_evans.vocabulary import BillEvansVocabularyIndex
from music_intelligence.legends.parker.vocabulary import ParkerVocabularyIndex


def _drum_rhythm_item():
    return VocabularyMemoryItem(
        vocabulary_id="DR-RHY-001",
        source_id="drum-solo-test",
        source_instrument="drums",
        dimensions=frozenset({
            VocabularyDimension.RHYTHM,
            VocabularyDimension.ACCENT,
            VocabularyDimension.DENSITY_ARC,
            VocabularyDimension.PHRASE_SHAPE,
        }),
        transferable_to=frozenset({"piano", "sax", "bass", "drums"}),
        candidate_uses=frozenset({
            VocabularyUseType.ABSTRACTED_PATTERN,
            VocabularyUseType.HYBRID_COMPOSITION,
        }),
        confidence=.9,
    )


def test_source_instrument_does_not_own_vocabulary():
    idx = BillEvansVocabularyIndex((_drum_rhythm_item(),))
    result = idx.query(VocabularyQuery(
        legend_id="bill_evans",
        target_instrument="piano",
        required_dimensions=frozenset({VocabularyDimension.RHYTHM}),
    ))
    assert result and result[0].source_instrument == "drums"


def test_target_player_can_request_only_transferable_dimensions():
    idx = ParkerVocabularyIndex((_drum_rhythm_item(),))
    # Wrong legend keeps normal provider ownership semantics.
    assert idx.query(VocabularyQuery(
        legend_id="charlie_parker",
        target_instrument="piano",
        required_dimensions=frozenset({VocabularyDimension.PITCH_INTERVAL}),
    )) == ()


def test_transfer_filter_blocks_unsupported_target():
    item = VocabularyMemoryItem(
        vocabulary_id="P-ONLY-001",
        source_id="test",
        source_instrument="piano",
        dimensions=frozenset({VocabularyDimension.RHYTHM}),
        transferable_to=frozenset({"piano", "sax"}),
    )
    idx = BillEvansVocabularyIndex((item,))
    assert idx.query(VocabularyQuery(
        legend_id="bill_evans",
        target_instrument="bass",
        required_dimensions=frozenset({VocabularyDimension.RHYTHM}),
    )) == ()
