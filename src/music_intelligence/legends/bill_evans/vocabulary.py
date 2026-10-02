"""Bill Evans vocabulary memory interface.

Bill Evans owns source/provenance. Shared Vocabulary owns reusable retrieval and
cross-instrument ranking.
"""
from __future__ import annotations
from dataclasses import dataclass

from music_intelligence.legends.interfaces import VocabularyMemoryItem, VocabularyQuery
from music_intelligence.vocabulary import rank_vocabulary_items


@dataclass(frozen=True)
class BillEvansVocabularyIndex:
    items: tuple[VocabularyMemoryItem, ...] = ()

    def query(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem, ...]:
        if request.legend_id != "bill_evans":
            return ()
        return rank_vocabulary_items(self.items, request)


BILL_EVANS_VOCABULARY_INDEX = BillEvansVocabularyIndex()
