"""Runtime projection of canonical Legend vocabularies.

No vocabulary truth is stored here. The composite provider only queries the
canonical per-Legend providers and merges ranked results for realtime consumers.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from music_intelligence.legends.interfaces import (
    LegendDomain,
    VocabularyMemoryItem,
    VocabularyProvider,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.vocabulary.usage_policy import choose_runtime_vocabulary_use
from .runtime_legend_resources import legend_runtime_resources


_LEGEND_IDS=("bill_evans","charlie_parker","scott_lafaro")


@dataclass(frozen=True)
class CompositeVocabularyProvider:
    legend_ids: tuple[str,...]=_LEGEND_IDS

    def query(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem,...]:
        rows: list[VocabularyMemoryItem]=[]
        seen=set()
        for legend_id in self.legend_ids:
            provider=legend_runtime_resources(legend_id).vocabulary_provider
            local=provider.query(replace(request,legend_id=legend_id))
            for item in local:
                if item.vocabulary_id in seen:
                    continue
                seen.add(item.vocabulary_id)
                rows.append(item)
        rows.sort(key=lambda x:(x.confidence,x.vocabulary_id),reverse=True)
        return tuple(rows[:request.limit])


SHARED_VOCABULARY_PROVIDER=CompositeVocabularyProvider()


@dataclass(frozen=True)
class RuntimeVocabularySelection:
    item: VocabularyMemoryItem
    use_type: VocabularyUseType


@dataclass(frozen=True)
class SharedVocabularyProjection:
    player_id: str
    target_instrument: str
    items: tuple[VocabularyMemoryItem,...]

    def ids(self) -> tuple[str,...]:
        return tuple(x.vocabulary_id for x in self.items)

    def tag_bias(self,tags: set[str] | frozenset[str]) -> float:
        active=set(tags)
        value=0.0
        for item in self.items:
            overlap=active.intersection(item.context_tags)
            if overlap:
                value += min(.055,.012*len(overlap))*item.confidence
        return max(-.20,min(.20,value))

    def items_for_domain(self,domain: LegendDomain) -> tuple[VocabularyMemoryItem,...]:
        return tuple(x for x in self.items if not x.domains or domain in x.domains)

    def runtime_selections(
        self,
        *,
        opportunity_index: int,
        allowed_uses: frozenset[VocabularyUseType]=frozenset(VocabularyUseType),
    ) -> tuple[RuntimeVocabularySelection,...]:
        """Project retrieved items through the one canonical reuse policy."""
        request=VocabularyQuery(
            legend_id="shared",
            target_instrument=self.target_instrument,
            allowed_uses=allowed_uses,
            limit=max(1,len(self.items)),
        )
        return tuple(
            RuntimeVocabularySelection(
                item,
                choose_runtime_vocabulary_use(
                    item,
                    request,
                    opportunity_index=opportunity_index+offset,
                ),
            )
            for offset,item in enumerate(self.items)
        )


def project_shared_vocabulary(
    provider: VocabularyProvider=SHARED_VOCABULARY_PROVIDER,
    *,
    player_id: str,
    target_instrument: str,
    domains: tuple[LegendDomain,...]=(),
    limit_per_domain: int=6,
) -> SharedVocabularyProjection:
    if not 1 <= limit_per_domain <= 16:
        raise ValueError("limit_per_domain must be within 1..16")
    requests=domains or (None,)
    gathered=[]
    seen=set()
    for domain in requests:
        rows=provider.query(VocabularyQuery(
            legend_id="shared",
            domain=domain,
            target_instrument=target_instrument,
            allowed_uses=frozenset({
                VocabularyUseType.LITERAL_QUOTE,
                VocabularyUseType.TRANSPOSED_LICK,
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
    return SharedVocabularyProjection(player_id,target_instrument,tuple(gathered))
