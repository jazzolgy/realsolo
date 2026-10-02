"""Charlie Parker vocabulary-memory contracts.

Literal licks are legitimate jazz memory. This module does not ship a copyrighted
lick corpus; it defines how Parker vocabulary can be indexed and queried, including
literal quotation, transposition, adaptation, fragmentation, abstraction and hybrid
composition.
"""
from music_intelligence.legends.interfaces import (
    VocabularyCandidateFamily,
    VocabularyIndex,
    VocabularyItem,
    VocabularyMatch,
    VocabularyQuery,
)

PARKER_LEGEND_ID = "charlie_parker"


def parker_vocabulary_item(**kwargs) -> VocabularyItem:
    kwargs.setdefault("legend_id", PARKER_LEGEND_ID)
    item = VocabularyItem(**kwargs)
    item.validate()
    return item


__all__ = [
    "PARKER_LEGEND_ID",
    "VocabularyCandidateFamily",
    "VocabularyIndex",
    "VocabularyItem",
    "VocabularyMatch",
    "VocabularyQuery",
    "parker_vocabulary_item",
]
