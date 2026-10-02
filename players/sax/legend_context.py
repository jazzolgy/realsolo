"""Legend-memory adapter for the Sax player.

This module is intentionally legend-agnostic.  Parker, Rollins, Coltrane, or
future profiles are injected through the shared Legend Intelligence interfaces.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.legends import (
    LegendDomain,
    LegendProfileView,
    VocabularyMemoryItem,
    VocabularyProvider,
    VocabularyQuery,
    VocabularyUseType,
)


@dataclass(frozen=True)
class SaxLegendContext:
    profile_view: LegendProfileView
    vocabulary_provider: VocabularyProvider

    def tendencies(
        self,
        *,
        domain: LegendDomain,
        active_tags: tuple[str, ...] = (),
    ):
        return self.profile_view.tendencies(domain=domain, active_tags=active_tags)

    def vocabulary(
        self,
        *,
        domain: LegendDomain | None = None,
        harmony_context: str = "",
        local_key: str = "",
        phrase_position: str = "",
        context_tags: frozenset[str] = frozenset(),
        allowed_uses: frozenset[VocabularyUseType] = frozenset(VocabularyUseType),
        limit: int = 16,
    ) -> tuple[VocabularyMemoryItem, ...]:
        request = VocabularyQuery(
            legend_id=self.profile_view.legend_id,
            domain=domain,
            harmony_context=harmony_context,
            local_key=local_key,
            phrase_position=phrase_position,
            context_tags=context_tags,
            allowed_uses=allowed_uses,
            limit=limit,
        )
        return self.vocabulary_provider.query(request)


@dataclass(frozen=True)
class SaxMemoryIntention:
    """Soft memory intention only; never a frozen future phrase."""

    use_type: VocabularyUseType
    active_vocabulary_ids: tuple[str, ...] = ()
    target: str = ""
    direction: str = "stable"
    interaction_role: str = ""

    def validate(self) -> None:
        if len(self.active_vocabulary_ids) > 8:
            raise ValueError("too many simultaneous vocabulary memories")
