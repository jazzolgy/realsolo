from music_intelligence.learning.admission import (
    EvidenceTrustClass,
    LearningAdmissionPolicy,
    admission_for_artifact,
)
from music_intelligence.learning.representation import LearningArtifact, LearningDomain
from music_intelligence.transcribe.evidence_diagnostics import (
    CorrectionRiskLevel,
    DistributionShift,
    EventCorrectionReport,
)


def _artifact(event_id="event:1"):
    return LearningArtifact(
        artifact_id="artifact:1",
        source_id="source:1",
        domain=LearningDomain.VOCABULARY,
        feature_schema="test.v1",
        features={"step_fraction": .7},
        source_event_ids=(event_id,),
        confidence=.9,
    )


def _report(level, review=False):
    shift = DistributionShift(
        domain="instrument",
        tv_distance=.6 if level is CorrectionRiskLevel.HIGH else .25,
        raw_top_label="kick",
        raw_top_probability=.55,
        posterior_top_label="bass",
        posterior_top_probability=.86,
        posterior_label_raw_support=.28,
        posterior_label_lift=.58,
        top_label_changed=True,
        context_dominated=level is CorrectionRiskLevel.HIGH,
        risk_level=level,
        review_recommended=review,
        reasons=(),
    )
    return EventCorrectionReport("event:1", instrument_shift=shift)


def test_high_context_risk_is_stored_but_not_admitted_to_priors():
    decision = admission_for_artifact(
        _artifact(),
        {"event:1": _report(CorrectionRiskLevel.HIGH, review=True)},
        rights_training_eligible=True,
    )
    assert decision.trust_class is EvidenceTrustClass.REVIEW_REQUIRED
    assert not decision.admit_to_evidence_prior
    assert not decision.admit_to_training_prior
    assert decision.requires_review


def test_moderate_context_supported_evidence_can_enter_priors_when_rights_allow():
    decision = admission_for_artifact(
        _artifact(),
        {"event:1": _report(CorrectionRiskLevel.MODERATE)},
        rights_training_eligible=True,
    )
    assert decision.trust_class is EvidenceTrustClass.CONTEXT_SUPPORTED
    assert decision.admit_to_evidence_prior
    assert decision.admit_to_training_prior


def test_rights_gate_remains_independent_of_evidence_quality():
    report = EventCorrectionReport("event:1")
    decision = admission_for_artifact(
        _artifact(),
        {"event:1": report},
        rights_training_eligible=False,
    )
    assert decision.trust_class is EvidenceTrustClass.DIRECT_ACOUSTIC
    assert decision.admit_to_evidence_prior
    assert not decision.admit_to_training_prior


def test_unassessed_legacy_artifact_is_evidence_only_by_default():
    decision = admission_for_artifact(
        _artifact(),
        {},
        rights_training_eligible=True,
    )
    assert decision.trust_class is EvidenceTrustClass.UNASSESSED
    assert decision.admit_to_evidence_prior
    assert not decision.admit_to_training_prior


def test_policy_can_block_context_supported_training():
    decision = admission_for_artifact(
        _artifact(),
        {"event:1": _report(CorrectionRiskLevel.MODERATE)},
        rights_training_eligible=True,
        policy=LearningAdmissionPolicy(allow_context_supported_training=False),
    )
    assert decision.admit_to_evidence_prior
    assert not decision.admit_to_training_prior
