"""Shared evidence gate for Legend vocabulary promotion.

Research observations may be stored freely with provenance. Runtime vocabulary
requires stronger evidence. This module keeps that distinction explicit and
instrument-neutral.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .interfaces import VocabularyMemoryItem


class VocabularyPromotionStatus(str, Enum):
    OBSERVATION_ONLY = "observation_only"
    VOCABULARY_CANDIDATE = "vocabulary_candidate"
    VALIDATED = "validated"
    ACTIVE_RUNTIME = "active_runtime"


@dataclass(frozen=True)
class VocabularyPromotionEvidence:
    """Evidence attached to one vocabulary hypothesis.

    independent_recording_count counts distinct verified recordings, not
    multiple windows cut from the same recording.
    """

    source_personnel_verified: bool = False
    phrase_context_verified: bool = False
    structural_coordinate_verified: bool = False
    arrangement_segment_verified: bool = False
    provenance_complete: bool = False
    dimension_confidence: float = 0.0
    detector_robustness: float = 0.0
    independent_window_count: int = 0
    independent_recording_count: int = 0
    manual_transcription_verified: bool = False
    isolated_or_separated_source: bool = False
    generic_pattern_risk: float = 0.0

    def validate(self) -> None:
        for name in (
            "dimension_confidence",
            "detector_robustness",
            "generic_pattern_risk",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.independent_window_count < 0:
            raise ValueError("independent_window_count may not be negative")
        if self.independent_recording_count < 0:
            raise ValueError("independent_recording_count may not be negative")


@dataclass(frozen=True)
class VocabularyPromotionDecision:
    status: VocabularyPromotionStatus
    eligible_for_runtime: bool
    reasons: tuple[str, ...]


def assess_vocabulary_promotion(
    item: VocabularyMemoryItem,
    evidence: VocabularyPromotionEvidence,
) -> VocabularyPromotionDecision:
    """Assess research evidence without changing the vocabulary item."""
    item.validate()
    evidence.validate()
    reasons: list[str] = []

    if not evidence.source_personnel_verified:
        reasons.append("source/personnel not verified")
    if not evidence.provenance_complete or not item.provenance:
        reasons.append("provenance incomplete")
    if not (
        evidence.structural_coordinate_verified
        or evidence.arrangement_segment_verified
    ):
        reasons.append("musical structural position not verified")

    base_ready = (
        evidence.source_personnel_verified
        and evidence.provenance_complete
        and bool(item.provenance)
        and (
            evidence.structural_coordinate_verified
            or evidence.arrangement_segment_verified
        )
        and evidence.dimension_confidence >= 0.80
    )
    if not base_ready:
        return VocabularyPromotionDecision(
            VocabularyPromotionStatus.OBSERVATION_ONLY,
            False,
            tuple(reasons or ("dimension confidence below vocabulary threshold",)),
        )

    if not evidence.phrase_context_verified:
        reasons.append("phrase/form context not verified")
    if evidence.detector_robustness < 0.75 and not (
        evidence.manual_transcription_verified
        or evidence.isolated_or_separated_source
    ):
        reasons.append("detector robustness below validation threshold")

    candidate_ready = evidence.phrase_context_verified
    if not candidate_ready:
        return VocabularyPromotionDecision(
            VocabularyPromotionStatus.VOCABULARY_CANDIDATE,
            False,
            tuple(reasons),
        )

    strong_event_evidence = (
        evidence.manual_transcription_verified
        or evidence.isolated_or_separated_source
        or evidence.detector_robustness >= 0.75
    )
    recurrence = (
        evidence.independent_recording_count >= 2
        or evidence.independent_window_count >= 2
    )
    if not strong_event_evidence or not recurrence:
        if not recurrence:
            reasons.append("independent recurrence not established")
        return VocabularyPromotionDecision(
            VocabularyPromotionStatus.VOCABULARY_CANDIDATE,
            False,
            tuple(reasons),
        )

    if evidence.generic_pattern_risk >= 0.75:
        reasons.append("pattern is too generic for legend-specific runtime use")
        return VocabularyPromotionDecision(
            VocabularyPromotionStatus.VALIDATED,
            False,
            tuple(reasons),
        )

    return VocabularyPromotionDecision(
        VocabularyPromotionStatus.ACTIVE_RUNTIME,
        True,
        ("independent and context-grounded evidence satisfies runtime gate",),
    )


def active_runtime_items(
    items: tuple[VocabularyMemoryItem, ...],
    evidence_by_id: dict[str, VocabularyPromotionEvidence],
) -> tuple[VocabularyMemoryItem, ...]:
    """Return only items that pass the common runtime promotion gate."""
    out: list[VocabularyMemoryItem] = []
    for item in items:
        evidence = evidence_by_id.get(item.vocabulary_id)
        if evidence is None:
            continue
        if assess_vocabulary_promotion(item, evidence).eligible_for_runtime:
            out.append(item)
    return tuple(out)
