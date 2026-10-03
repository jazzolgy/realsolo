"""YouTube research-provider boundary.

The adapter returns normal provider metadata and an embeddable video id. It does
not expose or download media bytes. Playback is expected to occur through a
visible embedded player in the research UI.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .research_listener import ResearchSourceCandidate


@dataclass(frozen=True)
class YouTubeSearchQuery:
    terms: str
    max_results: int = 12

    def validate(self) -> None:
        if not self.terms.strip():
            raise ValueError("search terms are required")
        if not 1 <= self.max_results <= 50:
            raise ValueError("max_results must be within 1..50")


@dataclass(frozen=True)
class YouTubeSearchResult:
    video_id: str
    title: str
    channel_title: str
    duration_s: float | None = None
    embeddable: bool = False
    playable: bool = False
    identity_confidence: float = 0.0
    source_reliability: float = 0.0
    audio_suitability: float = 0.0
    metadata: dict[str,object] | None = None

    def to_candidate(self, *, artist: str, coverage_gap_score: float) -> ResearchSourceCandidate:
        return ResearchSourceCandidate(
            source_id=f"youtube:{self.video_id}",
            provider="youtube",
            title=self.title,
            artist=artist,
            duration_s=self.duration_s,
            embeddable=self.embeddable,
            playable=self.playable,
            identity_confidence=self.identity_confidence,
            source_reliability=self.source_reliability,
            audio_suitability=self.audio_suitability,
            coverage_gap_score=coverage_gap_score,
            metadata={
                "video_id":self.video_id,
                "channel_title":self.channel_title,
                **(self.metadata or {}),
            },
        )


class YouTubeSearchProvider(Protocol):
    def search(self, query: YouTubeSearchQuery) -> Sequence[YouTubeSearchResult]: ...


def youtube_embed_url(video_id: str) -> str:
    if not video_id or any(ch.isspace() for ch in video_id):
        raise ValueError("invalid YouTube video id")
    return f"https://www.youtube.com/embed/{video_id}?enablejsapi=1"
