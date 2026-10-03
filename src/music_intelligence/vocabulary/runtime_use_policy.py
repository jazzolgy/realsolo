"""Runtime policy for direct vs transformed vocabulary use.

Project default:
- 30% direct/literal use when an item has an admitted literal representation.
- 70% transformed use (transposed/adapted/fragment/abstract/hybrid).
- If literal material is unavailable, the slot falls back to transformed use.

The ratio is a usage policy, not a requirement that every 10-event window be
exactly 3/7. A deterministic slot function keeps tests/rehearsals reproducible.
"""
from __future__ import annotations

from music_intelligence.legends.interfaces import (
    VocabularyMemoryItem,
    VocabularyUseType,
)

DIRECT_USE_SHARE = 0.30

_TRANSFORM_ORDER = (
    VocabularyUseType.HYBRID_COMPOSITION,
    VocabularyUseType.ABSTRACTED_PATTERN,
    VocabularyUseType.FRAGMENT_RECALL,
    VocabularyUseType.ADAPTED_LICK,
    VocabularyUseType.TRANSPOSED_LICK,
)


def choose_runtime_vocabulary_use(
    item: VocabularyMemoryItem,
    *,
    sequence_index: int,
) -> VocabularyUseType:
    """Choose direct vs transformed reuse for one vocabulary opportunity.

    Slots 0, 1, 2 of each ten-opportunity cycle are reserved for direct use
    when the item actually contains literal material and permits quotation.
    """

    item.validate()
    if sequence_index < 0:
        raise ValueError("sequence_index may not be negative")

    direct_slot=(sequence_index % 10) < 3
    if (
        direct_slot
        and item.literal_representation
        and VocabularyUseType.LITERAL_QUOTE in item.candidate_uses
    ):
        return VocabularyUseType.LITERAL_QUOTE

    for use in _TRANSFORM_ORDER:
        if use in item.candidate_uses:
            return use

    if (
        item.literal_representation
        and VocabularyUseType.LITERAL_QUOTE in item.candidate_uses
    ):
        return VocabularyUseType.LITERAL_QUOTE

    raise ValueError(f"no supported runtime use for {item.vocabulary_id}")
