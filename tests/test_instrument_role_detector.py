from realtime.ensemble_app.instrument_role_detector import (
    AcousticDescriptorFrame,
    BaselineInstrumentRoleDetector,
    TemporalContextCorrector,
)


def test_drum_like_frame_keeps_uncertainty():
    detector=BaselineInstrumentRoleDetector()
    raw=detector.detect(AcousticDescriptorFrame(
        pitch_hz=None,
        pitch_confidence=.05,
        onset=True,
        onset_strength=.8,
        rms=.2,
        spectral_centroid_hz=4200,
        spectral_flatness=.72,
        zero_crossing_rate=.18,
        low_energy_ratio=.12,
        mid_energy_ratio=.31,
        high_energy_ratio=.57,
    ))
    assert raw.instrument_probabilities["drums"] > .25
    assert sum(raw.instrument_probabilities.values()) <= .920001
    assert "trumpet" not in raw.instrument_probabilities


def test_bass_family_is_not_forced_acoustic_or_electric():
    detector=BaselineInstrumentRoleDetector()
    raw=detector.detect(AcousticDescriptorFrame(
        pitch_hz=82.4,
        pitch_confidence=.9,
        onset=True,
        onset_strength=.4,
        rms=.15,
        spectral_centroid_hz=700,
        spectral_flatness=.08,
        zero_crossing_rate=.03,
        low_energy_ratio=.75,
        mid_energy_ratio=.22,
        high_energy_ratio=.03,
    ))
    assert raw.instrument_probabilities["acoustic_bass"] == raw.instrument_probabilities["electric_bass"]
    assert raw.role_probabilities["bass_line"] > .2


def test_simple_pitched_descriptor_does_not_fake_named_horn_identity():
    detector=BaselineInstrumentRoleDetector()
    raw=detector.detect(AcousticDescriptorFrame(
        pitch_hz=523.25,
        pitch_confidence=.92,
        onset=True,
        onset_strength=.35,
        rms=.1,
        spectral_centroid_hz=2100,
        spectral_flatness=.12,
        zero_crossing_rate=.06,
        low_energy_ratio=.08,
        mid_energy_ratio=.80,
        high_energy_ratio=.12,
    ))
    assert "unknown_pitched" in raw.instrument_probabilities
    for named in ("trumpet","saxophone","flute","vocal","guitar","piano"):
        assert named not in raw.instrument_probabilities


def test_temporal_correction_cannot_create_missing_instrument_label():
    detector=BaselineInstrumentRoleDetector()
    corrector=TemporalContextCorrector()
    first=detector.detect(AcousticDescriptorFrame(
        pitch_hz=110.0,pitch_confidence=.8,onset=True,onset_strength=.3,rms=.1,
        low_energy_ratio=.7,mid_energy_ratio=.25,high_energy_ratio=.05,
        spectral_flatness=.05,zero_crossing_rate=.02,spectral_centroid_hz=800,
    ))
    post=corrector.correct(first)
    assert set(post.instrument_probabilities) == set(first.instrument_probabilities)
    assert post.confidence_fields["contextual_correction_magnitude"] <= .18
