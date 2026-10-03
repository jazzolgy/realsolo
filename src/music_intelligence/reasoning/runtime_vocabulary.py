"""Runtime projection of canonical source-grounded Vocabulary.

LegendProfile tendencies and Vocabulary memory are intentionally independent:
an empty LegendProfile does not imply an empty VocabularyProvider.

All ranking/reuse pressure remains owned by music_intelligence.vocabulary,
including the reconciliation policy in usage_policy. This module only selects
providers and projects already-ranked memories into player runtime context.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from music_intelligence.legends.interfaces import (
    LegendDomain,
    VocabularyMemoryItem,
    VocabularyProvider,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.legends.parker import PARKER_VOCABULARY_INDEX
from music_intelligence.legends.bill_evans import BILL_EVANS_VOCABULARY_INDEX
from music_intelligence.legends.scott_lafaro import SCOTT_LAFARO_VOCABULARY_INDEX


@dataclass(frozen=True)
class RuntimeVocabularySource:
    player_id: str
    legend_id: str
    provider: VocabularyProvider
    weight: float
    reason: str

    def validate(self) -> None:
        if not self.player_id or not self.legend_id:
            raise ValueError("player_id and legend_id are required")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("weight must be within 0..1")


@dataclass(frozen=True)
class SharedVocabularyProjection:
    player_id: str
    target_instrument: str
    items: tuple[VocabularyMemoryItem, ...]
    source_legend_ids: tuple[str, ...] = ()

    def ids(self) -> tuple[str, ...]:
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
        return tuple(x for x in self.items if not x.domains or domain in x.domains)


_REGISTRY: dict[str,VocabularyProvider] = {
    "charlie_parker": PARKER_VOCABULARY_INDEX,
    "bill_evans": BILL_EVANS_VOCABULARY_INDEX,
    "scott_lafaro": SCOTT_LAFARO_VOCABULARY_INDEX,
}


def _has_items(provider: VocabularyProvider) -> bool:
    items=getattr(provider,"items",())
    return bool(items)


def select_runtime_vocabulary_sources(
    *,
    overrides: Mapping[str,str] | None = None,
    showcase: bool = False,
) -> tuple[RuntimeVocabularySource,...]:
    """Select memory sources without consulting LegendProfile usability.

    Normal mode is conservative: named vocabulary is activated only through an
    explicit player override. Showcase mode exposes every non-empty source to its
    natural player so research can be heard without fabricating profile tendencies.
    """
    out: list[RuntimeVocabularySource]=[]
    overrides=overrides or {}

    for player_id,legend_id in overrides.items():
        provider=_REGISTRY.get(str(legend_id))
        if provider is None or not _has_items(provider):
            continue
        out.append(RuntimeVocabularySource(
            player_id=player_id,
            legend_id=str(legend_id),
            provider=provider,
            weight=.55,
            reason="explicit runtime vocabulary override",
        ))

    if showcase:
        showcase_map=(
            ("piano","bill_evans"),
            ("bass","scott_lafaro"),
            ("sax","charlie_parker"),
        )
        selected={x.player_id for x in out}
        for player_id,legend_id in showcase_map:
            if player_id in selected:
                continue
            provider=_REGISTRY[legend_id]
            if not _has_items(provider):
                continue
            out.append(RuntimeVocabularySource(
                player_id=player_id,
                legend_id=legend_id,
                provider=provider,
                weight=1.0,
                reason="vocabulary showcase: source-grounded memory",
            ))

    for item in out:
        item.validate()
    return tuple(out)


def project_runtime_vocabulary(
    sources: tuple[RuntimeVocabularySource,...],
    *,
    player_id: str,
    target_instrument: str,
    domains: tuple[LegendDomain,...]=(),
    harmony_context: str="",
    harmonic_function: str="",
    local_key: str="",
    phrase_position: str="",
    context_tags: frozenset[str]=frozenset(),
    limit_per_domain: int=6,
) -> SharedVocabularyProjection:
    if not 1 <= limit_per_domain <= 16:
        raise ValueError("limit_per_domain must be within 1..16")

    gathered: list[tuple[float,VocabularyMemoryItem,str]]=[]
    seen=set()
    requests=domains or (None,)

    for source in sources:
        if source.player_id != player_id:
            continue
        for domain in requests:
            rows=source.provider.query(VocabularyQuery(
                legend_id=source.legend_id,
                domain=domain,
                harmony_context=harmony_context,
                harmonic_function=harmonic_function,
                local_key=local_key,
                phrase_position=phrase_position,
                context_tags=context_tags,
                target_instrument=target_instrument,
                allowed_uses=frozenset(VocabularyUseType),
                limit=limit_per_domain,
            ))
            for item in rows:
                if item.vocabulary_id in seen:
                    continue
                seen.add(item.vocabulary_id)
                gathered.append((source.weight*item.confidence,item,source.legend_id))

    gathered.sort(key=lambda row:(row[0],row[1].vocabulary_id),reverse=True)
    items=tuple(row[1] for row in gathered)
    legends=tuple(dict.fromkeys(row[2] for row in gathered))
    return SharedVocabularyProjection(
        player_id=player_id,
        target_instrument=target_instrument,
        items=items,
        source_legend_ids=legends,
    )
