from music_intelligence.learning import (
    EvidenceTrustClass,
    LearningAdmissionDecision,
    LearningArtifact,
    LearningDomain,
    SharedLearningEngine,
)


def _artifact(artifact_id, value):
    return LearningArtifact(
        artifact_id=artifact_id,
        source_id="source:1",
        domain=LearningDomain.VOCABULARY,
        feature_schema="test.v1",
        features={"step_fraction": value},
        source_event_ids=(f"event:{artifact_id}",),
        confidence=.9,
    )


def test_review_required_artifact_is_stored_but_not_learned():
    engine = SharedLearningEngine()
    artifact = _artifact("review", .9)
    decision = LearningAdmissionDecision(
        artifact_id=artifact.artifact_id,
        trust_class=EvidenceTrustClass.REVIEW_REQUIRED,
        admit_to_evidence_prior=False,
        admit_to_training_prior=False,
        requires_review=True,
        reasons=("context-dominated",),
    )

    assert engine.ingest_artifacts_with_admission(
        (artifact,),
        {artifact.artifact_id: decision},
    ) == 1
    assert len(engine.store) == 1
    assert engine.evidence_prior(LearningDomain.VOCABULARY).observations == 0
    assert engine.prior(LearningDomain.VOCABULARY).observations == 0
    assert engine.review_required_artifacts() == (artifact,)


def test_context_supported_artifact_can_update_evidence_but_not_training_prior():
    engine = SharedLearningEngine()
    artifact = _artifact("context", .7)
    decision = LearningAdmissionDecision(
        artifact_id=artifact.artifact_id,
        trust_class=EvidenceTrustClass.CONTEXT_SUPPORTED,
        admit_to_evidence_prior=True,
        admit_to_training_prior=False,
        requires_review=False,
    )

    engine.ingest_artifacts_with_admission(
        (artifact,),
        {artifact.artifact_id: decision},
    )

    assert engine.evidence_prior(LearningDomain.VOCABULARY).observations == 1
    assert engine.prior(LearningDomain.VOCABULARY).observations == 0


def test_direct_acoustic_training_eligible_artifact_can_update_both_priors():
    engine = SharedLearningEngine()
    artifact = _artifact("direct", .5)
    decision = LearningAdmissionDecision(
        artifact_id=artifact.artifact_id,
        trust_class=EvidenceTrustClass.DIRECT_ACOUSTIC,
        admit_to_evidence_prior=True,
        admit_to_training_prior=True,
        requires_review=False,
    )

    engine.ingest_artifacts_with_admission(
        (artifact,),
        {artifact.artifact_id: decision},
    )

    assert engine.evidence_prior(LearningDomain.VOCABULARY).observations == 1
    assert engine.prior(LearningDomain.VOCABULARY).observations == 1


def test_admission_path_requires_explicit_decision_for_every_artifact():
    engine = SharedLearningEngine()
    artifact = _artifact("missing", .4)

    try:
        engine.ingest_artifacts_with_admission((artifact,), {})
    except ValueError as exc:
        assert "missing admission decision" in str(exc)
    else:
        raise AssertionError("admission-gated ingestion must not silently bypass policy")
