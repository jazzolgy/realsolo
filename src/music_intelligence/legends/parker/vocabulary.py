"""Charlie Parker vocabulary memory interface.

Parker owns the source/provenance of Parker vocabulary. Shared Vocabulary owns
cross-instrument filtering, affinity, repetition pressure and ranking.
"""
from __future__ import annotations
from dataclasses import dataclass

from music_intelligence.legends.interfaces import VocabularyMemoryItem, VocabularyQuery
from music_intelligence.vocabulary import rank_vocabulary_items


@dataclass(frozen=True)
class ParkerVocabularyIndex:
    items: tuple[VocabularyMemoryItem, ...] = ()

    def query(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem, ...]:
        if request.legend_id != "charlie_parker":
            return ()
        return rank_vocabulary_items(self.items, request)


PARKER_VOCABULARY_INDEX = ParkerVocabularyIndex()
