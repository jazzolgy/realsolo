import pytest

from realtime.ensemble_app.instrument_role_detector import AcousticDescriptorFrame
from realtime.ensemble_app.learned_instrument_adapter import (
    HybridInstrumentRoleDetector,
    LearnedInstrumentRoleAdapter,
)
from realtime.ensemble_app.model_service_backend import LocalInstrumentModelServiceBackend


def frame():
    return AcousticDescriptorFrame(
        pitch_hz=440.0,
        pitch_confidence=.8,
        onset=True,
        onset_strength=.35,
        rms=.1,
        spectral_centroid_hz=1800,
        spectral_flatness=.1,
        zero_crossing_rate=.04,
        low_energy_ratio=.1,
        mid_energy_ratio=.8,
        high_energy_ratio=.1,
    )


class FailingBackend:
    def predict(self, samples, *, sample_rate: int):
        raise RuntimeError("offline")


def test_remote_audio_model_is_rejected_by_default():
    with pytest.raises(ValueError):
        LocalInstrumentModelServiceBackend("https://example.com/v1/predict")


def test_local_audio_model_is_allowed():
    backend=LocalInstrumentModelServiceBackend("http://127.0.0.1:8788/v1/predict")
    assert backend.endpoint.startswith("http://127.0.0.1")


def test_failed_learned_backend_falls_back_to_baseline():
    detector=HybridInstrumentRoleDetector(
        learned=LearnedInstrumentRoleAdapter(FailingBackend())
    )
    raw=detector.detect([0.0],sample_rate=48000,frame=frame())
    assert raw.confidence_fields["learned_backend_available"] == 0.0
    assert raw.instrument_probabilities
