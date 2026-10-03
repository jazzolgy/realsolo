"""Source-separation contracts for autonomous research audio.

Separation is optional and in-memory. The RealSolo research listener does not
need to persist source media in order to use separated stems as analysis
evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence


@dataclass(frozen=True)
class SeparatedStem:
    stem_id: str
    samples: object
    sample_rate: int
    source_family: str = ""
    confidence: float = 0.0

    def validate(self) -> None:
        if not self.stem_id:
            raise ValueError("stem_id is required")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


class SourceSeparationBackend(Protocol):
    def separate(self, samples, *, sample_rate: int) -> Sequence[SeparatedStem]: ...


@dataclass(frozen=True)
class StemEvidenceSummary:
    stem_count: int
    stem_families: tuple[str,...]
    confidence_mean: float


def summarize_stems(stems: Sequence[SeparatedStem]) -> StemEvidenceSummary:
    if not stems:
        return StemEvidenceSummary(0,(),0.0)
    for stem in stems:
        stem.validate()
    families=tuple(sorted({x.source_family for x in stems if x.source_family}))
    return StemEvidenceSummary(
        stem_count=len(stems),
        stem_families=families,
        confidence_mean=sum(x.confidence for x in stems)/len(stems),
    )
