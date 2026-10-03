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
    """Policy thresholds and weights for learning admission.

    Weights are influence strengths, not probabilities and not truth labels.
    """

    allow_context_supported_training: bool = True
    allow_unassessed_evidence_prior: bool = True
    allow_unassessed_training_prior: bool = False

    direct_acoustic_weight: float = 1.0
    context_supported_weight: float = 0.65
    unassessed_evidence_weight: float = 0.50

    def validate(self) -> None:
        for name in (
            "direct_acoustic_weight",
            "context_supported_weight",
            "unassessed_evidence_weight",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


@dataclass(frozen=True)
class LearningAdmissionDecision:
    artifact_id: str
    trust_class: EvidenceTrustClass
    admit_to_evidence_prior: bool
    admit_to_training_prior: bool
    requires_review: bool
    evidence_weight: float = 0.0
    training_weight: float = 0.0
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.artifact_id:
            raise ValueError("artifact_id is required")
        if self.requires_review and self.admit_to_training_prior:
            raise ValueError("review-required evidence may not update training prior")
        if not 0.0 <= self.evidence_weight <= 1.0:
            raise ValueError("evidence_weight must be within 0..1")
        if not 0.0 <= self.training_weight <= 1.0:
            raise ValueError("training_weight must be within 0..1")
        if not self.admit_to_evidence_prior and self.evidence_weight != 0.0:
            raise ValueError("non-admitted evidence prior must have zero weight")
        if not self.admit_to_training_prior and self.training_weight != 0.0:
            raise ValueError("non-admitted training prior must have zero weight")


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
    policy.validate()
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
            evidence_weight=0.0,
            training_weight=0.0,
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
            evidence_weight=policy.context_supported_weight,
            training_weight=(
                policy.context_supported_weight
                if rights_training_eligible and policy.allow_context_supported_training
                else 0.0
            ),
            reasons=reasons,
        )
    elif trust is EvidenceTrustClass.DIRECT_ACOUSTIC:
        decision = LearningAdmissionDecision(
            artifact_id=artifact.artifact_id,
            trust_class=trust,
            admit_to_evidence_prior=True,
            admit_to_training_prior=rights_training_eligible,
            requires_review=False,
            evidence_weight=policy.direct_acoustic_weight,
            training_weight=(
                policy.direct_acoustic_weight if rights_training_eligible else 0.0
            ),
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
            evidence_weight=(
                policy.unassessed_evidence_weight
                if policy.allow_unassessed_evidence_prior
                else 0.0
            ),
            training_weight=(
                policy.unassessed_evidence_weight
                if rights_training_eligible and policy.allow_unassessed_training_prior
                else 0.0
            ),
            reasons=reasons,
        )

    decision.validate()
    return decision
