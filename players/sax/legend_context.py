"""Legend-memory adapter for the Sax player.

This module is intentionally legend-agnostic. Parker, Rollins, Coltrane, or
future profiles are injected through shared Legend Intelligence interfaces.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.legends import (
    ContextualLegendMixture,
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
    mixture: ContextualLegendMixture | None = None

    def tendencies(
        self,
        *,
        domain: LegendDomain,
        active_tags: tuple[str, ...] = (),
    ):
        return self.profile_view.tendencies(domain=domain, active_tags=active_tags)

    def feature_bias(
        self,
        *,
        domain: LegendDomain,
        feature: str,
        active_tags: tuple[str, ...] = (),
    ) -> float:
        if self.mixture is not None:
            return self.mixture.feature_bias(
                domain=domain,
                feature=feature,
                active_tags=active_tags,
            )
        total = 0.0
        for profile, profile_weight in self.profile_view.weighted_profiles():
            for tendency in profile.tendencies:
                if tendency.feature != feature:
                    continue
                if tendency.context_tags and not tendency.context_tags.issubset(set(active_tags)):
                    continue
                total += profile_weight * tendency.weight * tendency.confidence
        return total

    def vocabulary(
        self,
        *,
        domain: LegendDomain | None = None,
        harmony_context: str = "",
        harmonic_function: str = "",
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
            harmonic_function=harmonic_function,
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
