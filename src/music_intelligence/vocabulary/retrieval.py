"""Shared ranking for Legend vocabulary memories.

Legend providers own their data/provenance. This module owns reusable filtering
and soft ranking, including cross-instrument affinity.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.legends.interfaces import (
    VocabularyMemoryItem,
    VocabularyQuery,
)
from .affinity import vocabulary_affinity


@dataclass(frozen=True)
class VocabularyRankingBreakdown:
    confidence: float
    context_fit: float
    instrument_affinity: float
    dimension_affinity: float
    recent_use_penalty: float

    @property
    def total(self) -> float:
        return (
            self.confidence
            + self.context_fit
            + self.instrument_affinity
            + self.dimension_affinity
            - self.recent_use_penalty
        )


def _is_eligible(item: VocabularyMemoryItem, request: VocabularyQuery) -> bool:
    item.validate()
    if request.domain is not None and item.domains and request.domain not in item.domains:
        return False
    if not item.candidate_uses.intersection(request.allowed_uses):
        return False
    if request.context_tags and not request.context_tags.issubset(item.context_tags):
        return False
    if request.required_dimensions and not request.required_dimensions.issubset(item.dimensions):
        return False
    if (
        request.target_instrument
        and item.transferable_to
        and request.target_instrument not in item.transferable_to
    ):
        return False
    return True


def score_vocabulary_item(
    item: VocabularyMemoryItem,
    request: VocabularyQuery,
) -> VocabularyRankingBreakdown | None:
    if not _is_eligible(item, request):
        return None

    context_fit = 0.0
    for wanted, actual, reward in (
        (request.harmony_context, item.harmony_context, .12),
        (request.harmonic_function, item.harmonic_function, .12),
        (request.local_key, item.local_key, .06),
        (request.phrase_position, item.phrase_position, .08),
    ):
        if wanted:
            if actual == wanted:
                context_fit += reward
            elif actual:
                context_fit -= reward

    affinity = vocabulary_affinity(item, request)
    recent_use_penalty = min(.25, .04 * item.recent_usage_count)

    return VocabularyRankingBreakdown(
        confidence=item.confidence,
        context_fit=context_fit,
        instrument_affinity=affinity.source_instrument,
        dimension_affinity=affinity.dimensions,
        recent_use_penalty=recent_use_penalty,
    )


def rank_vocabulary_items(
    items: tuple[VocabularyMemoryItem, ...],
    request: VocabularyQuery,
) -> tuple[VocabularyMemoryItem, ...]:
    if request.limit <= 0:
        return ()

    ranked: list[tuple[float, VocabularyMemoryItem]] = []
    for item in items:
        score = score_vocabulary_item(item, request)
        if score is None:
            continue
        ranked.append((score.total, item))

    ranked.sort(
        key=lambda pair: (pair[0], pair[1].vocabulary_id),
        reverse=True,
    )
    return tuple(item for _, item in ranked[: request.limit])
