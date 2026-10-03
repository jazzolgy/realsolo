"""Shared score-aligned research evidence.

All instrument research should interpret audio-derived evidence at a musical
score/form location whenever a score/form anchor exists. Raw timestamps remain
source locators; they are not the primary learning coordinate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class AlignmentStatus(str, Enum):
    UNALIGNED = "unaligned"
    SECTION_ALIGNED = "section_aligned"
    BAR_ALIGNED = "bar_aligned"
    BEAT_ALIGNED = "beat_aligned"


class PerformancePhase(str, Enum):
    UNKNOWN = "unknown"
    INTRO = "intro"
    HEAD = "head"
    SOLO = "solo"
    BASS_FOREGROUND = "bass_foreground"
    DRUM_FOREGROUND = "drum_foreground"
    HEAD_OUT = "head_out"
    CODA = "coda"
    ENDING = "ending"


@dataclass(frozen=True)
class MusicalScoreCoordinate:
    """Canonical research coordinate shared by all instruments."""

    song_id: str
    score_source_id: str = ""
    page: int | None = None
    section: str = ""
    bar: int | None = None
    beat: float | None = None
    chorus_index: int | None = None
    performance_phase: PerformancePhase = PerformancePhase.UNKNOWN
    chord_label: str = ""
    harmonic_function: str = ""
    phrase_position: str = ""
    form_role: str = ""
    navigation_state: str = ""
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.song_id:
            raise ValueError("song_id is required")
        if self.page is not None and self.page < 1:
            raise ValueError("page must be 1-based")
        if self.bar is not None and self.bar < 1:
            raise ValueError("bar must be 1-based")
        if self.beat is not None:
            if self.bar is None:
                raise ValueError("beat requires bar")
            if self.beat < 0:
                raise ValueError("beat may not be negative")
        if self.chorus_index is not None and self.chorus_index < 0:
            raise ValueError("chorus_index may not be negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")

    @property
    def alignment_status(self) -> AlignmentStatus:
        if self.bar is not None and self.beat is not None:
            return AlignmentStatus.BEAT_ALIGNED
        if self.bar is not None:
            return AlignmentStatus.BAR_ALIGNED
        if self.section:
            return AlignmentStatus.SECTION_ALIGNED
        return AlignmentStatus.UNALIGNED


@dataclass(frozen=True)
class AudioScoreAlignment:
    """Map one source-audio window to one musical score/form coordinate."""

    source_id: str
    start_s: float
    end_s: float
    coordinate: MusicalScoreCoordinate
    alignment_confidence: float = 1.0
    method: str = ""
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.start_s < 0 or self.end_s <= self.start_s:
            raise ValueError("audio window must satisfy 0 <= start < end")
        if not 0.0 <= self.alignment_confidence <= 1.0:
            raise ValueError("alignment_confidence must be within 0..1")
        self.coordinate.validate()


@dataclass(frozen=True)
class ScoreAlignedEvidence:
    """Derived evidence interpreted at a musical location.

    Instrument may be empty for whole-ensemble evidence. Instrument attribution
    should be filled only when sufficiently verified.
    """

    evidence_id: str
    alignment: AudioScoreAlignment
    feature_schema: str
    features: Mapping[str, object] = field(default_factory=dict)
    instrument: str = ""
    ensemble_role: str = ""
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.evidence_id or not self.feature_schema:
            raise ValueError("evidence_id and feature_schema are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        self.alignment.validate()

    @property
    def eligible_for_position_comparison(self) -> bool:
        return self.alignment.coordinate.alignment_status is not AlignmentStatus.UNALIGNED


def same_musical_position(
    left: ScoreAlignedEvidence,
    right: ScoreAlignedEvidence,
    *,
    ignore_chorus: bool = True,
) -> bool:
    """Compare evidence by musical location rather than source timestamp."""
    left.validate()
    right.validate()
    a = left.alignment.coordinate
    b = right.alignment.coordinate
    if a.song_id != b.song_id:
        return False
    if a.section and b.section and a.section != b.section:
        return False
    if a.bar is not None and b.bar is not None and a.bar != b.bar:
        return False
    if a.beat is not None and b.beat is not None and a.beat != b.beat:
        return False
    if not ignore_chorus and a.chorus_index != b.chorus_index:
        return False
    return (
        a.alignment_status is not AlignmentStatus.UNALIGNED
        and b.alignment_status is not AlignmentStatus.UNALIGNED
    )


def research_learning_status(evidence: ScoreAlignedEvidence) -> str:
    """Unaligned evidence is navigation-only; aligned evidence may be studied."""
    evidence.validate()
    status = evidence.alignment.coordinate.alignment_status
    if status is AlignmentStatus.UNALIGNED:
        return "navigation_only"
    if status is AlignmentStatus.SECTION_ALIGNED:
        return "section_comparison"
    if status is AlignmentStatus.BAR_ALIGNED:
        return "bar_comparison"
    return "beat_comparison"
