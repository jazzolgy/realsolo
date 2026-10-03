"""Project Shared Vocabulary into current-player soft runtime cues."""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.legends.interfaces import (
    LegendDomain,
    VocabularyMemoryItem,
    VocabularyQuery,
    VocabularyUseType,
    VocabularyProvider,
)


@dataclass(frozen=True)
class SharedVocabularyProjection:
    player_id: str
    target_instrument: str
    items: tuple[VocabularyMemoryItem,...]

    def ids(self) -> tuple[str,...]:
        return tuple(x.vocabulary_id for x in self.items)

    def tag_bias(self, tags: set[str] | frozenset[str]) -> float:
        active=set(tags)
        value=0.0
        for item in self.items:
            overlap=active.intersection(item.context_tags)
            if overlap:
                value += min(.055,.012*len(overlap))*item.confidence
        return max(-.20,min(.20,value))

    def items_for_domain(self, domain: LegendDomain) -> tuple[VocabularyMemoryItem,...]:
        return tuple(
            x for x in self.items
            if not x.domains or domain in x.domains
        )


def project_shared_vocabulary(
    provider: VocabularyProvider,
    *,
    player_id: str,
    target_instrument: str,
    domains: tuple[LegendDomain,...]=(),
    limit_per_domain: int=6,
) -> SharedVocabularyProjection:
    if not 1 <= limit_per_domain <= 16:
        raise ValueError("limit_per_domain must be within 1..16")

    requests=domains or (None,)
    gathered: list[VocabularyMemoryItem]=[]
    seen=set()
    for domain in requests:
        rows=provider.query(VocabularyQuery(
            legend_id="shared",
            domain=domain,
            target_instrument=target_instrument,
            allowed_uses=frozenset({
                VocabularyUseType.ADAPTED_LICK,
                VocabularyUseType.FRAGMENT_RECALL,
                VocabularyUseType.ABSTRACTED_PATTERN,
                VocabularyUseType.HYBRID_COMPOSITION,
            }),
            limit=limit_per_domain,
        ))
        for item in rows:
            if item.vocabulary_id in seen:
                continue
            seen.add(item.vocabulary_id)
            gathered.append(item)

    return SharedVocabularyProjection(
        player_id=player_id,
        target_instrument=target_instrument,
        items=tuple(gathered),
    )
