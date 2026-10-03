"""Research queue contracts for semi-autonomous legend listening.

This module deliberately does not fetch or extract provider media. It represents
approved/searchable sources and decides which eligible source should be studied next.
Playback and user-authorized audio capture belong to the realtime/web boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence


class ResearchSourceState(str, Enum):
    DISCOVERED = "discovered"
    ELIGIBLE = "eligible"
    QUEUED = "queued"
    PLAYING = "playing"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass(frozen=True)
class ResearchSourceCandidate:
    source_id: str
    provider: str
    title: str
    artist: str
    duration_s: float | None = None
    embeddable: bool = False
    playable: bool = False
    identity_confidence: float = 0.0
    source_reliability: float = 0.0
    audio_suitability: float = 0.0
    coverage_gap_score: float = 0.0
    duplicate_penalty: float = 0.0
    recent_use_penalty: float = 0.0
    metadata: Mapping[str, object] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if not self.provider:
            raise ValueError("provider is required")
        if self.duration_s is not None and self.duration_s <= 0:
            raise ValueError("duration_s must be positive when known")
        for name in (
            "identity_confidence",
            "source_reliability",
            "audio_suitability",
            "coverage_gap_score",
            "duplicate_penalty",
            "recent_use_penalty",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")

    @property
    def eligible(self) -> bool:
        return self.embeddable and self.playable


@dataclass(frozen=True)
class ResearchListenerPolicy:
    min_identity_confidence: float = 0.70
    min_source_reliability: float = 0.55
    min_audio_suitability: float = 0.45
    min_duration_s: float = 45.0
    max_duration_s: float = 4 * 60 * 60.0
    weight_identity: float = 0.20
    weight_reliability: float = 0.15
    weight_audio: float = 0.20
    weight_gap: float = 0.45
    weight_duplicate_penalty: float = 0.35
    weight_recent_penalty: float = 0.20

    def allows(self, candidate: ResearchSourceCandidate) -> bool:
        candidate.validate()
        if not candidate.eligible:
            return False
        if candidate.identity_confidence < self.min_identity_confidence:
            return False
        if candidate.source_reliability < self.min_source_reliability:
            return False
        if candidate.audio_suitability < self.min_audio_suitability:
            return False
        if candidate.duration_s is not None:
            if candidate.duration_s < self.min_duration_s:
                return False
            if candidate.duration_s > self.max_duration_s:
                return False
        return True

    def score(self, candidate: ResearchSourceCandidate) -> float:
        if not self.allows(candidate):
            return float("-inf")
        return (
            self.weight_identity * candidate.identity_confidence
            + self.weight_reliability * candidate.source_reliability
            + self.weight_audio * candidate.audio_suitability
            + self.weight_gap * candidate.coverage_gap_score
            - self.weight_duplicate_penalty * candidate.duplicate_penalty
            - self.weight_recent_penalty * candidate.recent_use_penalty
        )


def rank_research_candidates(
    candidates: Sequence[ResearchSourceCandidate],
    policy: ResearchListenerPolicy | None = None,
) -> tuple[ResearchSourceCandidate, ...]:
    """Return eligible candidates ordered by research value.

    Stable source_id ordering makes equal-score results deterministic.
    """

    policy = policy or ResearchListenerPolicy()
    eligible = [c for c in candidates if policy.allows(c)]
    return tuple(
        sorted(
            eligible,
            key=lambda c: (-policy.score(c), c.source_id),
        )
    )


def choose_next_research_source(
    candidates: Sequence[ResearchSourceCandidate],
    policy: ResearchListenerPolicy | None = None,
) -> ResearchSourceCandidate | None:
    ranked = rank_research_candidates(candidates, policy)
    return ranked[0] if ranked else None
