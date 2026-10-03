import numpy as np

from realtime.ensemble_app.yamnet_instrument_backend import YAMNetInstrumentBackend


class TensorLike:
    def __init__(self,value):
        self._value=np.asarray(value,dtype=np.float32)
    def numpy(self):
        return self._value


class FakeYAMNet:
    def __call__(self,waveform):
        # Trumpet, Saxophone, Singing
        return (
            TensorLike([[.80,.20,.35],[.70,.30,.45]]),
            TensorLike([[0.0],[0.0]]),
            TensorLike([[0.0]]),
        )


def test_yamnet_waits_for_minimum_window_without_loading_model():
    backend=YAMNetInstrumentBackend(min_window_s=.96)
    instruments,roles,confidence=backend.predict(
        np.zeros(4000,dtype=np.float32),
        sample_rate=16000,
    )
    assert instruments == {}
    assert roles == {}
    assert confidence["yamnet_window_ready"] == 0.0


def test_yamnet_maps_audioset_classes_to_realsolo_instruments():
    backend=YAMNetInstrumentBackend(min_window_s=.96)
    backend._model=FakeYAMNet()
    backend._class_names=("Trumpet","Saxophone","Singing")
    instruments,roles,confidence=backend.predict(
        np.zeros(16000,dtype=np.float32),
        sample_rate=16000,
    )
    assert instruments["trumpet"] > instruments["saxophone"]
    assert instruments["vocal"] > 0
    assert roles == {}
    assert confidence["yamnet_window_ready"] == 1.0
    assert confidence["yamnet_instrument"] == max(instruments.values())


def test_yamnet_resamples_browser_rate_before_inference():
    seen={}
    class CaptureModel:
        def __call__(self,waveform):
            seen["samples"]=len(waveform)
            return (
                TensorLike([[.5]]),
                TensorLike([[0.0]]),
                TensorLike([[0.0]]),
            )
    backend=YAMNetInstrumentBackend(min_window_s=.96,analysis_window_s=.96)
    backend._model=CaptureModel()
    backend._class_names=("Piano",)
    instruments,_,_=backend.predict(
        np.zeros(48000,dtype=np.float32),
        sample_rate=48000,
    )
    assert seen["samples"] == 16000
    assert instruments["piano"] > 0


def test_explicit_label_teaches_latest_embedding(tmp_path):
    backend=YAMNetInstrumentBackend(
        min_window_s=.96,
        adaptation_path=tmp_path/"head.json",
    )
    backend._model=FakeYAMNet()
    backend._class_names=("Trumpet","Saxophone","Singing")
    backend.predict(np.zeros(16000,dtype=np.float32),sample_rate=16000)
    assert backend.admit_explicit_label("trumpet") is True
    assert backend.adaptation_counts()["trumpet"] >= 1


def test_explicit_label_rejects_unknown_baseline_label(tmp_path):
    backend=YAMNetInstrumentBackend(
        min_window_s=.96,
        adaptation_path=tmp_path/"head.json",
    )
    backend._model=FakeYAMNet()
    backend._class_names=("Trumpet","Saxophone","Singing")
    backend.predict(np.zeros(16000,dtype=np.float32),sample_rate=16000)
    import pytest
    with pytest.raises(ValueError):
        backend.admit_explicit_label("mystery horn")
