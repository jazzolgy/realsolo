from music_intelligence.legends.interfaces import VocabularyUseType, VocabularyQuery
from music_intelligence.vocabulary import SHARED_VOCABULARY_INDEX
from music_intelligence.vocabulary.runtime_use_policy import (
    DIRECT_USE_SHARE,
    choose_runtime_vocabulary_use,
)


def _literal_item():
    rows=SHARED_VOCABULARY_INDEX.query(VocabularyQuery(
        legend_id="shared",
        target_instrument="drums",
        limit=64,
    ))
    return next(x for x in rows if x.literal_representation)


def test_direct_use_share_is_thirty_percent():
    assert DIRECT_USE_SHARE == .30


def test_exact_source_patterns_are_in_shared_vocabulary():
    item=_literal_item()
    assert item.literal_representation
    assert VocabularyUseType.LITERAL_QUOTE in item.candidate_uses
    assert "exact_symbolic_source_pattern" in item.provenance


def test_runtime_policy_uses_literal_on_three_of_ten_slots_when_available():
    item=_literal_item()
    uses=[
        choose_runtime_vocabulary_use(item,sequence_index=i)
        for i in range(10)
    ]
    assert uses.count(VocabularyUseType.LITERAL_QUOTE)==3


def test_nonliteral_item_falls_back_to_transformation_even_on_direct_slot():
    rows=SHARED_VOCABULARY_INDEX.query(VocabularyQuery(
        legend_id="shared",
        target_instrument="tenor_sax",
        limit=64,
    ))
    item=next(x for x in rows if not x.literal_representation)
    assert choose_runtime_vocabulary_use(item,sequence_index=0) is not VocabularyUseType.LITERAL_QUOTE
