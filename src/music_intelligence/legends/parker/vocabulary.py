"""Charlie Parker vocabulary memory interface.

Stored licks, motifs, fragments, cliches, and quotations are legitimate jazz
memory. The public repository may contain metadata/derived evidence while literal
payloads can remain in the private corpus when source rights require it.
"""
from __future__ import annotations
from dataclasses import dataclass

from music_intelligence.legends.interfaces import VocabularyMemoryItem, VocabularyQuery


@dataclass(frozen=True)
class ParkerVocabularyIndex:
    items: tuple[VocabularyMemoryItem, ...] = ()

    def query(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem, ...]:
        if request.legend_id != "charlie_parker" or request.limit <= 0:
            return ()

        ranked: list[tuple[float, VocabularyMemoryItem]] = []
        for item in self.items:
            item.validate()
            if request.domain is not None and item.domains and request.domain not in item.domains:
                continue
            if not item.candidate_uses.intersection(request.allowed_uses):
                continue
            if request.context_tags and not request.context_tags.issubset(item.context_tags):
                continue

            score = item.confidence
            for wanted, actual, reward in (
                (request.harmony_context, item.harmony_context, .12),
                (request.harmonic_function, item.harmonic_function, .12),
                (request.local_key, item.local_key, .06),
                (request.phrase_position, item.phrase_position, .08),
            ):
                if wanted:
                    if actual == wanted:
                        score += reward
                    elif actual:
                        score -= reward

            if item.recent_usage_count:
                score -= min(.25, .04 * item.recent_usage_count)
            ranked.append((score, item))

        ranked.sort(key=lambda pair: (pair[0], pair[1].vocabulary_id), reverse=True)
        return tuple(item for _, item in ranked[: request.limit])


PARKER_VOCABULARY_INDEX = ParkerVocabularyIndex()
