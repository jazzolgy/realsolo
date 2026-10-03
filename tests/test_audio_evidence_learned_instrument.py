from __future__ import annotations

from pathlib import Path

import pytest

from music_intelligence.audio_evidence.adapters.source import AudioSource
from music_intelligence.audio_evidence.detectors import (
    DetectorFeatureEncoder,
    LearnedInstrumentClassifier,
    OnsetDetection,
    PitchDetection,
    TimbreDetection,
    UnpitchedDetection,
)
from music_intelligence.audio_evidence.detectors.torchscript_instrument import (
    TorchScriptInstrumentBackend,
)


class FakeLearnedBackend:
    backend_id = "fake-learned:v1"

    def predict_probabilities(self, features):
        result = []
        for feature in features:
            if feature.values[3] == 1.0:
                result.append({"drums": 0.91, "other": 0.09})
            elif feature.values[0] < 55.0:
                result.append({"bass": 0.52, "piano": 0.43, "other": 0.05})
            else:
                result.append({"piano": 0.93, "bass": 0.04, "other": 0.03})
        return tuple(result)


def fixtures():
    onsets = (
        OnsetDetection(onset_id="o1", onset_seconds=1.0, confidence=0.95),
        OnsetDetection(onset_id="o2", onset_seconds=2.0, confidence=0.92),
    )
    pitches = (
        PitchDetection(
            onset_id="o1",
            pitch_id="p-low",
            nominal_midi=48.0,
            frequency_hz=130.81,
            confidence=0.90,
        ),
        PitchDetection(
            onset_id="o2",
            pitch_id="p-high",
            nominal_midi=72.0,
            frequency_hz=523.25,
            confidence=0.94,
        ),
    )
    unpitched = (
        UnpitchedDetection(onset_id="o2", token="snare", confidence=0.88),
    )
    timbre = (
        TimbreDetection(
            onset_id="o1",
            spectral_centroid_hz=1100.0,
            features={"flatness": 0.11},
        ),
        TimbreDetection(
            onset_id="o2",
            spectral_centroid_hz=2600.0,
            features={"flatness": 0.36},
        ),
    )
    return onsets, pitches, unpitched, timbre


def test_detector_feature_encoder_preserves_target_specific_acoustic_features():
    onsets, pitches, unpitched, timbre = fixtures()
    encoder = DetectorFeatureEncoder()

    features = encoder.encode(
        AudioSource(source_id="mix"),
        onsets,
        pitches,
        unpitched,
        timbre,
    )

    assert len(features) == 3
    assert features[0].target_id == "p-low"
    assert "spectral_centroid_hz" in features[0].feature_names
    assert "timbre:flatness" in features[0].feature_names
    assert features[-1].target_id == "o2:unpitched:1"
    assert features[-1].values[3] == 1.0


def test_learned_classifier_keeps_low_register_ambiguity_from_backend():
    onsets, pitches, unpitched, timbre = fixtures()
    classifier = LearnedInstrumentClassifier(backend=FakeLearnedBackend())

    detections = classifier.detect_instruments(
        AudioSource(source_id="mix"),
        onsets,
        pitches,
        unpitched,
        timbre,
    )

    low = next(item for item in detections if item.target_id == "p-low")
    high = next(item for item in detections if item.target_id == "p-high")
    drum = next(item for item in detections if item.target_id == "o2:unpitched:1")

    assert low.probabilities["bass"] == pytest.approx(0.52)
    assert low.probabilities["piano"] == pytest.approx(0.43)
    assert low.confidence == pytest.approx(0.09)
    assert high.probabilities["piano"] == pytest.approx(0.93)
    assert drum.probabilities["drums"] == pytest.approx(0.91)
    assert "fake-learned:v1" in low.detector_id


def test_torchscript_backend_does_not_import_torch_until_prediction(tmp_path: Path):
    model = tmp_path / "instrument.pt"
    model.write_bytes(b"placeholder")

    backend = TorchScriptInstrumentBackend(
        model_path=str(model),
        class_labels=("bass", "piano", "other"),
    )

    assert backend.class_labels == ("bass", "piano", "other")
    assert backend._model is None


def test_torchscript_backend_rejects_missing_model_before_torch_import(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        TorchScriptInstrumentBackend(
            model_path=str(tmp_path / "missing.pt"),
            class_labels=("bass", "piano"),
        )
