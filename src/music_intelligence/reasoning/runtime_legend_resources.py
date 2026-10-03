"""Canonical runtime access to Legend profiles and vocabularies.

Profile tendencies and vocabulary availability are deliberately independent:
an empty LegendProfile does not imply an empty VocabularyProvider, and vice
versa. Runtime/Player code consumes this registry; it does not recreate legend
research state.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.legends.interfaces import (
    LegendProfileView,
    VocabularyMemoryItem,
    VocabularyProvider,
    VocabularyQuery,
)
from music_intelligence.legends.bill_evans import (
    BILL_EVANS_PROFILE_VIEW,
    BILL_EVANS_VOCABULARY_INDEX,
)
from music_intelligence.legends.parker import (
    PARKER_PROFILE_VIEW,
    PARKER_VOCABULARY_INDEX,
)
from music_intelligence.legends.scott_lafaro import (
    SCOTT_LAFARO_PROFILE_VIEW,
    SCOTT_LAFARO_VOCABULARY_INDEX,
)


@dataclass(frozen=True)
class LegendRuntimeResources:
    legend_id: str
    profile_view: LegendProfileView
    vocabulary_provider: VocabularyProvider

    @property
    def profile_available(self) -> bool:
        return any(
            profile.source_count > 0 and bool(profile.tendencies)
            for profile,_weight in self.profile_view.weighted_profiles()
        )

    def vocabulary(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem,...]:
        if request.legend_id != self.legend_id:
            return ()
        return self.vocabulary_provider.query(request)

    def vocabulary_available(self, *, target_instrument: str = "") -> bool:
        rows=self.vocabulary_provider.query(VocabularyQuery(
            legend_id=self.legend_id,
            target_instrument=target_instrument,
            limit=1,
        ))
        return bool(rows)


_REGISTRY: dict[str,LegendRuntimeResources] = {
    "charlie_parker": LegendRuntimeResources(
        "charlie_parker", PARKER_PROFILE_VIEW, PARKER_VOCABULARY_INDEX
    ),
    "bill_evans": LegendRuntimeResources(
        "bill_evans", BILL_EVANS_PROFILE_VIEW, BILL_EVANS_VOCABULARY_INDEX
    ),
    "scott_lafaro": LegendRuntimeResources(
        "scott_lafaro", SCOTT_LAFARO_PROFILE_VIEW, SCOTT_LAFARO_VOCABULARY_INDEX
    ),
}


def legend_runtime_resources(legend_id: str) -> LegendRuntimeResources:
    try:
        return _REGISTRY[legend_id]
    except KeyError as exc:
        raise KeyError(f"unknown legend_id: {legend_id}") from exc
