"""Scott LaFaro provenance-aware vocabulary interface."""
from __future__ import annotations
from dataclasses import dataclass

from music_intelligence.legends.interfaces import VocabularyMemoryItem, VocabularyQuery
from music_intelligence.vocabulary import rank_vocabulary_items


@dataclass(frozen=True)
class ScottLaFaroVocabularyIndex:
    items: tuple[VocabularyMemoryItem, ...] = ()

    def query(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem, ...]:
        if request.legend_id != "scott_lafaro":
            return ()
        return rank_vocabulary_items(self.items, request)


SCOTT_LAFARO_VOCABULARY_INDEX = ScottLaFaroVocabularyIndex()
