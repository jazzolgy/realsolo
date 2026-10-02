"""Bill Evans vocabulary memory interface.

Literal phrases, voicings, motifs, rhythmic cells, comping fragments, and other
memory items are allowed once they are source-grounded and provenance-tagged.
The index starts empty until observations are promoted.
"""
from __future__ import annotations
from dataclasses import dataclass

from music_intelligence.legends.interfaces import VocabularyMemoryItem, VocabularyQuery


@dataclass(frozen=True)
class BillEvansVocabularyIndex:
    items: tuple[VocabularyMemoryItem, ...] = ()

    def query(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem, ...]:
        if request.legend_id != "bill_evans" or request.limit <= 0:
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
            if request.required_dimensions and not request.required_dimensions.issubset(item.dimensions):
                continue
            if (
                request.target_instrument
                and item.transferable_to
                and request.target_instrument not in item.transferable_to
            ):
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


BILL_EVANS_VOCABULARY_INDEX = BillEvansVocabularyIndex()
