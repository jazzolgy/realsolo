"""Admission policy from Performance Evidence diagnostics into learning/memory.

This module does not decide whether an interpretation is musically true.
It decides how cautiously evidence may influence shared learning priors.

All artifacts remain storable/auditable. Admission controls whether they may
update evidence priors or trainable/adaptive priors.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from music_intelligence.transcribe.evidence_diagnostics import (
    CorrectionRiskLevel,
    EventCorrectionReport,
)

from .representation import LearningArtifact


class EvidenceTrustClass(str, Enum):
    DIRECT_ACOUSTIC = "direct_acoustic"
    CONTEXT_SUPPORTED = "context_supported"
    REVIEW_REQUIRED = "review_required"
    UNASSESSED = "unassessed"


@dataclass(frozen=True)
class LearningAdmissionPolicy:
    """Policy thresholds for deciding how evidence may update learning state."""

    allow_context_supported_training: bool = True
    allow_unassessed_evidence_prior: bool = True
    allow_unassessed_training_prior: bool = False


@dataclass(frozen=True)
class LearningAdmissionDecision:
    artifact_id: str
    trust_class: EvidenceTrustClass
    admit_to_evidence_prior: bool
    admit_to_training_prior: bool
    requires_review: bool
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.artifact_id:
            raise ValueError("artifact_id is required")
        if self.requires_review and self.admit_to_training_prior:
            raise ValueError("review-required evidence may not update training prior")


def _risk_rank(level: CorrectionRiskLevel) -> int:
    return {
        CorrectionRiskLevel.NONE: 0,
        CorrectionRiskLevel.LOW: 1,
        CorrectionRiskLevel.MODERATE: 2,
        CorrectionRiskLevel.HIGH: 3,
    }[level]


def classify_reports(
    reports: tuple[EventCorrectionReport, ...],
) -> tuple[EvidenceTrustClass, tuple[str, ...]]:
    """Classify evidence without erasing raw/posterior detail."""

    if not reports:
        return EvidenceTrustClass.UNASSESSED, ("no-correction-diagnostics",)

    if any(report.review_recommended or report.max_risk is CorrectionRiskLevel.HIGH for report in reports):
        return (
            EvidenceTrustClass.REVIEW_REQUIRED,
            ("high-or-review-recommended-context-correction",),
        )

    max_risk = max((report.max_risk for report in reports), key=_risk_rank)
    if max_risk is CorrectionRiskLevel.NONE:
        return EvidenceTrustClass.DIRECT_ACOUSTIC, ("raw-and-context-agree",)

    if max_risk is CorrectionRiskLevel.LOW:
        return EvidenceTrustClass.DIRECT_ACOUSTIC, ("small-context-correction",)

    return (
        EvidenceTrustClass.CONTEXT_SUPPORTED,
        ("moderate-context-correction",),
    )


def admission_for_artifact(
    artifact: LearningArtifact,
    reports_by_event_id: Mapping[str, EventCorrectionReport],
    *,
    rights_training_eligible: bool,
    policy: LearningAdmissionPolicy = LearningAdmissionPolicy(),
) -> LearningAdmissionDecision:
    """Decide prior admission from source-event correction diagnostics.

    Rights and evidence quality are independent gates:
    even high-quality evidence cannot enter the trainable prior without rights.
    """

    artifact.validate()
    reports = tuple(
        reports_by_event_id[event_id]
        for event_id in artifact.source_event_ids
        if event_id in reports_by_event_id
    )
    trust, reasons = classify_reports(reports)

    if trust is EvidenceTrustClass.REVIEW_REQUIRED:
        decision = LearningAdmissionDecision(
            artifact_id=artifact.artifact_id,
            trust_class=trust,
            admit_to_evidence_prior=False,
            admit_to_training_prior=False,
            requires_review=True,
            reasons=reasons + ("stored-for-audit-not-prior-update",),
        )
    elif trust is EvidenceTrustClass.CONTEXT_SUPPORTED:
        decision = LearningAdmissionDecision(
            artifact_id=artifact.artifact_id,
            trust_class=trust,
            admit_to_evidence_prior=True,
            admit_to_training_prior=(
                rights_training_eligible and policy.allow_context_supported_training
            ),
            requires_review=False,
            reasons=reasons,
        )
    elif trust is EvidenceTrustClass.DIRECT_ACOUSTIC:
        decision = LearningAdmissionDecision(
            artifact_id=artifact.artifact_id,
            trust_class=trust,
            admit_to_evidence_prior=True,
            admit_to_training_prior=rights_training_eligible,
            requires_review=False,
            reasons=reasons,
        )
    else:
        decision = LearningAdmissionDecision(
            artifact_id=artifact.artifact_id,
            trust_class=trust,
            admit_to_evidence_prior=policy.allow_unassessed_evidence_prior,
            admit_to_training_prior=(
                rights_training_eligible and policy.allow_unassessed_training_prior
            ),
            requires_review=False,
            reasons=reasons,
        )

    decision.validate()
    return decision
