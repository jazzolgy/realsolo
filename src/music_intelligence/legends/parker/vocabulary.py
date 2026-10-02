"""Charlie Parker vocabulary memory interface.

Stored licks, motifs, fragments, cliches, and quotations are legitimate jazz
memory.  The public repository currently contains aggregate/derived evidence,
not the private literal source corpus.
"""
from __future__ import annotations
from dataclasses import dataclass

from music_intelligence.legends.interfaces import VocabularyMemoryItem, VocabularyQuery


@dataclass(frozen=True)
class ParkerVocabularyIndex:
    items: tuple[VocabularyMemoryItem, ...] = ()

    def query(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem, ...]:
        if request.legend_id != "charlie_parker":
            return ()
        items = self.items
        if request.harmony_context:
            items = tuple(i for i in items if not i.harmony_context or i.harmony_context == request.harmony_context)
        if request.local_key:
            items = tuple(i for i in items if not i.local_key or i.local_key == request.local_key)
        if request.phrase_position:
            items = tuple(i for i in items if not i.phrase_position or i.phrase_position == request.phrase_position)
        return items[: request.limit]


PARKER_VOCABULARY_INDEX = ParkerVocabularyIndex()
