"""Expression-profile memory kept separate from note/vocabulary identity.

One vocabulary/motif identity may have multiple observed expression profiles.
Retrieval chooses an expression profile independently from pitch/rhythm content.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .expressive_realization import ExpressionProfile


@dataclass
class ExpressionProfileStore:
    _by_source: dict[str,list[ExpressionProfile]] = field(default_factory=dict)

    def add(self, profile: ExpressionProfile) -> None:
        profile.validate()
        bucket=self._by_source.setdefault(profile.source_identity,[])
        if any(x.profile_id==profile.profile_id for x in bucket):
            return
        bucket.append(profile)

    def profiles_for(self, source_identity: str) -> tuple[ExpressionProfile,...]:
        return tuple(self._by_source.get(source_identity,()))

    def choose(
        self,
        source_identity: str,
        *,
        prefer_contour: str="",
    ) -> ExpressionProfile | None:
        rows=list(self._by_source.get(source_identity,()))
        if not rows:
            return None
        if prefer_contour:
            matching=[x for x in rows if x.contour.value==prefer_contour]
            if matching:
                rows=matching
        return max(rows,key=lambda x:(x.confidence,x.profile_id))
