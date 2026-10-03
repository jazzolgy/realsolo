from music_intelligence.learning import (
    LearningDomain,SharedLearningEngine,
    artifacts_from_audio_aggregate,
)


def test_unaligned_audio_aggregate_remains_navigation_only():
    payload={
        "sources":[{
            "source_id":"private.bill_evans.test",
            "confidence_mean":.8,
            "onset_rate_p10":1.0,"onset_rate_p50":3.0,"onset_rate_p90":5.0,
            "rms_p10":.1,"rms_p50":.2,"rms_p90":.3,
            "pitch_class_entropy_norm":.9,
            "same_pitch_transition_fraction":.2,
            "step_motion_fraction":.3,
            "within_fifth_motion_fraction":.7,
            "octave_or_more_motion_fraction":.1,
        }]
    }
    artifacts=artifacts_from_audio_aggregate(payload)
    engine=SharedLearningEngine()
    assert engine.ingest_artifacts(artifacts,learn=False,study_as_evidence=True)==3
    assert len(engine.store)==3
    assert engine.prior(LearningDomain.VOCABULARY).observations==0
    # Timestamp/global acoustic evidence may help navigation, but it does not
    # become a musical prior until form/section/bar/beat alignment exists.
    assert engine.evidence_prior(LearningDomain.VOCABULARY).observations==0
