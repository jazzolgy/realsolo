import pytest

from music_intelligence.learning import (
    EvidenceTrustClass,
    LearningAdmissionDecision,
    LearningAdmissionPolicy,
    LearningArtifact,
    LearningDomain,
    SharedLearningEngine,
)
from music_intelligence.learning.admission import admission_for_artifact
from music_intelligence.transcribe.evidence_diagnostics import (
    CorrectionRiskLevel,
    DistributionShift,
    EventCorrectionReport,
)


def _artifact(artifact_id: str, value: float, *, confidence: float = 1.0):
    return LearningArtifact(
        artifact_id=artifact_id,
        source_id="source:1",
        domain=LearningDomain.VOCABULARY,
        feature_schema="weighted.test.v1",
        features={"step_fraction": value, "shape": "ascending" if value > .5 else "flat"},
        source_event_ids=(f"event:{artifact_id}",),
        confidence=confidence,
    )


def _moderate_report(event_id: str):
    shift = DistributionShift(
        domain="instrument",
        tv_distance=.30,
        raw_top_label="bass",
        raw_top_probability=.48,
        posterior_top_label="bass",
        posterior_top_probability=.70,
        posterior_label_raw_support=.48,
        posterior_label_lift=.22,
        top_label_changed=False,
        context_dominated=False,
        risk_level=CorrectionRiskLevel.MODERATE,
        review_recommended=False,
        reasons=("moderate_distribution_shift",),
    )
    return EventCorrectionReport(event_id, instrument_shift=shift)


def test_context_supported_admission_uses_configurable_weight():
    artifact = _artifact("ctx", .8)
    decision = admission_for_artifact(
        artifact,
        {"event:ctx": _moderate_report("event:ctx")},
        rights_training_eligible=True,
        policy=LearningAdmissionPolicy(context_supported_weight=.60),
    )

    assert decision.trust_class is EvidenceTrustClass.CONTEXT_SUPPORTED
    assert decision.evidence_weight == pytest.approx(.60)
    assert decision.training_weight == pytest.approx(.60)


def test_weighted_numeric_mean_prevents_weak_context_evidence_from_counting_full_strength():
    engine = SharedLearningEngine()

    direct = _artifact("direct", .2, confidence=1.0)
    context = _artifact("context", 1.0, confidence=1.0)

    engine.ingest_artifacts_with_admission(
        (direct, context),
        {
            "direct": LearningAdmissionDecision(
                artifact_id="direct",
                trust_class=EvidenceTrustClass.DIRECT_ACOUSTIC,
                admit_to_evidence_prior=True,
                admit_to_training_prior=False,
                requires_review=False,
                evidence_weight=1.0,
                training_weight=0.0,
            ),
            "context": LearningAdmissionDecision(
                artifact_id="context",
                trust_class=EvidenceTrustClass.CONTEXT_SUPPORTED,
                admit_to_evidence_prior=True,
                admit_to_training_prior=False,
                requires_review=False,
                evidence_weight=.5,
                training_weight=0.0,
            ),
        },
    )

    prior = engine.evidence_prior(LearningDomain.VOCABULARY)
    assert prior.observations == 2
    assert prior.weighted_observations == pytest.approx(1.5)
    assert prior.numeric_features["step_fraction"] == pytest.approx((.2*1.0 + 1.0*.5) / 1.5)


def test_artifact_confidence_multiplies_admission_weight():
    engine = SharedLearningEngine()
    artifact = _artifact("weak", .9, confidence=.4)
    decision = LearningAdmissionDecision(
        artifact_id="weak",
        trust_class=EvidenceTrustClass.CONTEXT_SUPPORTED,
        admit_to_evidence_prior=True,
        admit_to_training_prior=False,
        requires_review=False,
        evidence_weight=.5,
        training_weight=0.0,
    )

    engine.ingest_artifacts_with_admission((artifact,), {"weak": decision})
    prior = engine.evidence_prior(LearningDomain.VOCABULARY)

    assert prior.weighted_observations == pytest.approx(.2)
    assert prior.numeric_weights["step_fraction"] == pytest.approx(.2)


def test_weighted_categorical_prior_uses_influence_not_raw_count():
    engine = SharedLearningEngine()
    high = _artifact("high", .8)
    low = LearningArtifact(
        artifact_id="low",
        source_id="source:1",
        domain=LearningDomain.VOCABULARY,
        feature_schema="weighted.test.v1",
        features={"step_fraction": .3, "shape": "flat"},
        source_event_ids=("event:low",),
        confidence=1.0,
    )

    engine.ingest_artifacts_with_admission(
        (high, low),
        {
            "high": LearningAdmissionDecision(
                "high",
                EvidenceTrustClass.DIRECT_ACOUSTIC,
                True,
                False,
                False,
                evidence_weight=1.0,
                training_weight=0.0,
            ),
            "low": LearningAdmissionDecision(
                "low",
                EvidenceTrustClass.CONTEXT_SUPPORTED,
                True,
                False,
                False,
                evidence_weight=.25,
                training_weight=0.0,
            ),
        },
    )

    prior = engine.evidence_prior(LearningDomain.VOCABULARY)
    assert prior.categorical_counts["shape"]["ascending"] == 1
    assert prior.categorical_counts["shape"]["flat"] == 1
    assert prior.category_weight("shape", "ascending") == pytest.approx(.8)
    assert prior.category_weight("shape", "flat") == pytest.approx(.2)


def test_review_required_evidence_still_contributes_zero_weight():
    engine = SharedLearningEngine()
    artifact = _artifact("review", .95)
    decision = LearningAdmissionDecision(
        artifact_id="review",
        trust_class=EvidenceTrustClass.REVIEW_REQUIRED,
        admit_to_evidence_prior=False,
        admit_to_training_prior=False,
        requires_review=True,
        evidence_weight=0.0,
        training_weight=0.0,
    )
    engine.ingest_artifacts_with_admission((artifact,), {"review": decision})
    prior = engine.evidence_prior(LearningDomain.VOCABULARY)
    assert prior.observations == 0
    assert prior.weighted_observations == 0.0
