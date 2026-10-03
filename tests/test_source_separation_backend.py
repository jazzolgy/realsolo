import pytest

from realtime.ensemble_app.separation_service_backend import (
    LocalSourceSeparationServiceBackend,
)
from realtime.ensemble_app.source_separation import SeparatedStem
from realtime.ensemble_app.stem_aware_instrument_backend import StemAwareInstrumentBackend


class FakeSeparator:
    def separate(self, samples, *, sample_rate: int):
        return (
            SeparatedStem("horn",[0.1,0.2],sample_rate,"foreground",.9),
            SeparatedStem("rhythm",[0.1,0.1],sample_rate,"rhythm",.7),
        )


class FakeClassifier:
    def predict(self, samples, *, sample_rate: int):
        if samples[0] == 0.1 and samples[1] == 0.2:
            return ({"trumpet":.8},{"solo":.7},{"model":.9})
        return ({"drums":.6},{"timekeeping":.65},{"model":.8})


def test_remote_separator_rejected_by_default():
    with pytest.raises(ValueError):
        LocalSourceSeparationServiceBackend("https://example.com/v1/separate")


def test_stem_aware_backend_fuses_probabilities():
    backend=StemAwareInstrumentBackend(FakeSeparator(),FakeClassifier())
    instruments,roles,confidence=backend.predict([0.0],sample_rate=48000)
    assert instruments["trumpet"] > instruments["drums"]
    assert roles["solo"] > 0
    assert confidence["source_separation"] == pytest.approx(.8)


def test_stem_aware_backend_falls_back_when_no_stems():
    class EmptySeparator:
        def separate(self, samples, *, sample_rate: int):
            return ()
    backend=StemAwareInstrumentBackend(EmptySeparator(),FakeClassifier())
    instruments,roles,confidence=backend.predict([0.1,0.2],sample_rate=48000)
    assert instruments["trumpet"] == .8
