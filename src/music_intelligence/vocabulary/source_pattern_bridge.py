"""Promote exact symbolic source patterns into Shared Vocabulary.

This adapter does not schedule future music. It serializes already-ingested
symbolic source patterns into VocabularyMemoryItem records so retrieval can
select them. Runtime still commits only the current event/gesture.
"""
from __future__ import annotations

from music_intelligence.legends.interfaces import (
    LegendDomain,
    VocabularyDimension,
    VocabularyMemoryItem,
    VocabularyUseType,
)
from players.drums.pattern_corpus import PATTERN_CORPUS, StoredDrumPattern


def _serialize_hits(pattern: StoredDrumPattern) -> str:
    return ";".join(
        f"{hit.onset_beats:.6f}:{hit.voice.value}:{hit.velocity_class}:{hit.articulation}"
        for hit in pattern.hits
    )


def vocabulary_item_from_drum_pattern(pattern: StoredDrumPattern) -> VocabularyMemoryItem:
    pattern.validate()
    item=VocabularyMemoryItem(
        vocabulary_id=f"source_pattern:{pattern.pattern_id}",
        source_id=f"source_corpus:{pattern.pattern_id}",
        literal_representation=_serialize_hits(pattern),
        transposition_normalized_representation=_serialize_hits(pattern),
        rhythm=f"{pattern.length_beats:g}-beat symbolic drum pattern",
        articulation=" ".join(sorted({hit.articulation for hit in pattern.hits})),
        source_instrument="drums",
        dimensions=frozenset({
            VocabularyDimension.RHYTHM,
            VocabularyDimension.ARTICULATION,
            VocabularyDimension.ACCENT,
        }),
        transferable_to=frozenset({"drums"}),
        domains=frozenset({
            LegendDomain.RHYTHM_SUBDIVISION,
            LegendDomain.ARTICULATION,
            LegendDomain.FORM_AWARENESS,
        }),
        context_tags=frozenset(pattern.tags),
        candidate_uses=frozenset({
            VocabularyUseType.LITERAL_QUOTE,
            VocabularyUseType.ADAPTED_LICK,
            VocabularyUseType.FRAGMENT_RECALL,
            VocabularyUseType.ABSTRACTED_PATTERN,
            VocabularyUseType.HYBRID_COMPOSITION,
        }),
        confidence=.98,
        provenance=(
            "players/drums/pattern_corpus.py",
            pattern.source.source_title,
            pattern.source.source_page,
            "exact_symbolic_source_pattern",
        ),
    )
    item.validate()
    return item


SOURCE_PATTERN_VOCABULARY_ITEMS=tuple(
    vocabulary_item_from_drum_pattern(pattern)
    for pattern in PATTERN_CORPUS
)
