from music_intelligence.learning.shared_audio_intelligence import (
    ContextCorrection,
    DetectorEvidence,
    MusicalMoment,
    PerformanceEvidence,
    identity_context_correction,
    musical_moment_from_evidence,
    structural_event_from_evidence,
)


def test_unknown_musical_moment_values_are_none_not_zero():
    raw=DetectorEvidence(
        pitch_hz=440.0,
        onset=True,
        confidence_fields={"pitch":.9,"event":.8},
    )
    ev=PerformanceEvidence(
        source_id="youtube:x",
        timestamp_s=12.0,
        raw=raw,
        posterior=identity_context_correction(raw),
    )
    moment=musical_moment_from_evidence(ev)
    assert moment.density is None
    assert moment.tension is None
    assert moment.register_center is None


def test_raw_and_context_posterior_remain_distinct():
    raw=DetectorEvidence(
        instrument_probabilities={"bass":.55,"kick":.35},
        role_probabilities={"walking":.45,"unknown":.4},
        confidence_fields={"instrument":.55},
        onset=True,
    )
    posterior=ContextCorrection(
        instrument_probabilities={"bass":.86,"kick":.10},
        role_probabilities={"walking":.82,"unknown":.12},
        confidence_fields={"instrument":.86,"role":.82,"event":.8},
        reasons=("walking_continuity","shared_groove_match"),
    )
    ev=PerformanceEvidence("youtube:x",3.0,raw,posterior)
    assert ev.raw.instrument_probabilities["bass"] == .55
    assert ev.posterior.instrument_probabilities["bass"] == .86


def test_structural_promotion_waits_for_beat_alignment():
    raw=DetectorEvidence(pitch_hz=440.0,onset=True,confidence_fields={"pitch":.9})
    ev=PerformanceEvidence("youtube:x",1.0,raw,identity_context_correction(raw))
    assert structural_event_from_evidence(ev,event_id="e1",onset_beats=None,duration_beats=None) is None


def test_structural_event_preserves_probability_fields():
    raw=DetectorEvidence(
        instrument_probabilities={"trumpet":.7,"saxophone":.2},
        role_probabilities={"solo":.8,"ensemble":.1},
        confidence_fields={"pitch":.9,"event":.81},
        pitch_hz=440.0,
        onset=True,
    )
    posterior=ContextCorrection(
        instrument_probabilities={"trumpet":.82,"saxophone":.1},
        role_probabilities={"solo":.9,"ensemble":.05},
        confidence_fields={"instrument":.82,"role":.9,"event":.84},
        reasons=("phrase_role_context",),
    )
    ev=PerformanceEvidence("youtube:x",1.0,raw,posterior)
    structural=structural_event_from_evidence(
        ev,event_id="e1",onset_beats=2.0,duration_beats=.5
    )
    assert structural is not None
    assert structural.instrument == "trumpet"
    assert structural.role == "solo"
    assert structural.confidence == .84
    assert structural.instrument_probabilities["trumpet"] == .82
