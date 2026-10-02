"""Domain/context-aware mixture across multiple LegendProfileView objects."""
from __future__ import annotations
from dataclasses import dataclass

from .interfaces import LegendDomain, LegendProfileView


@dataclass(frozen=True)
class LegendViewWeight:
    view: LegendProfileView
    weight: float = 1.0


@dataclass(frozen=True)
class ContextualLegendMixture:
    views: tuple[LegendViewWeight, ...]

    def feature_bias(
        self,
        *,
        domain: LegendDomain,
        feature: str,
        active_tags: tuple[str, ...] = (),
    ) -> float:
        total = 0.0
        for weighted in self.views:
            if weighted.weight < 0:
                raise ValueError("legend mixture weights cannot be negative")
            for tendency in weighted.view.tendencies(domain=domain, active_tags=active_tags):
                if tendency.feature != feature:
                    continue
                source_weight = 1.0
                for profile, profile_weight in weighted.view.weighted_profiles():
                    if tendency in profile.tendencies:
                        source_weight = profile_weight
                        break
                total += weighted.weight * source_weight * tendency.weight * tendency.confidence
        return total
