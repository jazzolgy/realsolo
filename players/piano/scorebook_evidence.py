"""Piano view over canonical Shared Scorebook Ingestion evidence.

This module does not parse score PDFs and does not redefine score evidence.
It only exposes canonical Core evidence to Piano policy/runtime.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.corpus import (
    ScoreEvidenceKind,
    ScorebookSongLocator,
)


@dataclass(frozen=True)
class PianoScorebookEvidenceView:
    song_id: str = ""
    book_id: str = ""
    title: str = ""
    styles: tuple[str, ...] = ()
    feel_changes: tuple[str, ...] = ()
    section_roles: tuple[str, ...] = ()
    navigation: tuple[str, ...] = ()
    written_parts: tuple[str, ...] = ()
    arrangement_notes: tuple[str, ...] = ()
    evidence_confidence_floor: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not 0.0 <= self.evidence_confidence_floor <= 1.0:
            raise ValueError("evidence_confidence_floor must be within 0..1")


def build_piano_scorebook_evidence_view(
    song: ScorebookSongLocator,
) -> PianoScorebookEvidenceView:
    """Project canonical score evidence into a read-only Piano-facing view."""
    song.validate()

    buckets: dict[ScoreEvidenceKind, list[str]] = {
        ScoreEvidenceKind.STYLE: [],
        ScoreEvidenceKind.FEEL_CHANGE: [],
        ScoreEvidenceKind.SECTION_ROLE: [],
        ScoreEvidenceKind.NAVIGATION: [],
        ScoreEvidenceKind.WRITTEN_PART: [],
        ScoreEvidenceKind.ARRANGEMENT_NOTE: [],
    }
    confidences: list[float] = []
    provenance: list[str] = [
        f"scorebook_song:{song.song_id}",
        f"scorebook:{song.book_id}",
    ]

    for evidence in song.evidence:
        evidence.validate()
        confidences.append(evidence.confidence)
        provenance.extend(evidence.provenance)
        if evidence.source_page is not None:
            provenance.append(
                f"score_page:{song.book_id}:{evidence.source_page}"
            )
        if evidence.kind in buckets:
            buckets[evidence.kind].append(evidence.value)

    view = PianoScorebookEvidenceView(
        song_id=song.song_id,
        book_id=song.book_id,
        title=song.title,
        styles=tuple(buckets[ScoreEvidenceKind.STYLE]),
        feel_changes=tuple(buckets[ScoreEvidenceKind.FEEL_CHANGE]),
        section_roles=tuple(buckets[ScoreEvidenceKind.SECTION_ROLE]),
        navigation=tuple(buckets[ScoreEvidenceKind.NAVIGATION]),
        written_parts=tuple(buckets[ScoreEvidenceKind.WRITTEN_PART]),
        arrangement_notes=tuple(buckets[ScoreEvidenceKind.ARRANGEMENT_NOTE]),
        evidence_confidence_floor=min(confidences) if confidences else 1.0,
        provenance=tuple(dict.fromkeys(provenance)),
    )
    view.validate()
    return view
