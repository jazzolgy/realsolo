"""Promotion gate from measured written-part evidence to Bass runtime priors.

A qualitative page observation is useful research evidence but must not alter
candidate ranking as if it were a measured statistic. Only a numeric abstract
profile produced from structured note events may be promoted.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .scorebook_evidence import BassWrittenPartPrior
from .written_part_comparator import (
    BassLineAbstractProfile,
    written_part_prior_from_profile,
)


class WrittenPartMeasurementStatus(str, Enum):
    QUALITATIVE_ONLY = "qualitative_only"
    STRUCTURED_EVENTS = "structured_events"
    MEASURED_PROFILE = "measured_profile"
    VERIFIED_PROFILE = "verified_profile"


@dataclass(frozen=True)
class MeasuredWrittenPartEvidence:
    study_id: str
    song_id: str
    source_book_id: str
    source_page: int
    status: WrittenPartMeasurementStatus
    confidence: float
    profile: BassLineAbstractProfile | None = None
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.study_id or not self.song_id or not self.source_book_id:
            raise ValueError("written-part evidence identity is required")
        if self.source_page < 1:
            raise ValueError("source_page must be 1-based")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        if self.status in {
            WrittenPartMeasurementStatus.MEASURED_PROFILE,
            WrittenPartMeasurementStatus.VERIFIED_PROFILE,
        } and self.profile is None:
            raise ValueError("measured/verified status requires numeric profile")


def promote_written_part_prior(
    evidence: MeasuredWrittenPartEvidence,
    *,
    minimum_confidence: float = .85,
) -> BassWrittenPartPrior | None:
    """Promote only measured numeric evidence into a runtime ranking prior."""
    evidence.validate()
    if evidence.status not in {
        WrittenPartMeasurementStatus.MEASURED_PROFILE,
        WrittenPartMeasurementStatus.VERIFIED_PROFILE,
    }:
        return None
    if evidence.confidence < minimum_confidence:
        return None
    assert evidence.profile is not None
    return written_part_prior_from_profile(evidence.profile)
