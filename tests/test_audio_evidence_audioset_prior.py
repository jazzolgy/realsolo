from __future__ import annotations

import pytest

from music_intelligence.audio_evidence.adapters.source import AudioSource
from music_intelligence.audio_evidence.detectors import (
    AudioSetFrameScores,
    AudioSetInstrumentPriorDetector,
    OnsetDetection,
    PitchDetection,
    UnpitchedDetection,
    YAMNetAudioSetBackend,
)


class FakeAudioSetBackend:
    backend_id = "fake-audioset:v1"

    def score_onsets(self, source, onsets):
        return (
            AudioSetFrameScores(
                onset_id="o1",
                scores={
                    "Piano": 0.70,
                    "Double bass": 0.25,
                    "Drum kit": 0.05,
                },
            ),
            AudioSetFrameScores(
                onset_id="o2",
                scores={
                    "Piano": 0.08,
                    "Double bass": 0.10,
                    "Drum kit": 0.75,
                    "Snare drum": 0.55,
                },
            ),
        )


def test_audioset_tagger_is_used_only_as_weak_instrument_prior():
    detector = AudioSetInstrumentPriorDetector(
        backend=FakeAudioSetBackend(),
        prior_strength=0.35,
    )
    onsets = (
        OnsetDetection(onset_id="o1", onset_seconds=1.0, confidence=0.9),
        OnsetDetection(onset_id="o2", onset_seconds=2.0, confidence=0.9),
    )
    pitches = (
        PitchDetection(
            onset_id="o1",
            pitch_id="p1",
            nominal_midi=60.0,
            frequency_hz=261.63,
            confidence=0.9,
        ),
    )
    unpitched = (
        UnpitchedDetection(
            onset_id="o2",
            token="snare",
            confidence=0.9,
        ),
    )

    result = detector.detect_instruments(
        AudioSource(source_id="mix"),
        onsets,
        pitches,
        unpitched,
        (),
    )

    pitched = next(item for item in result if item.target_id == "p1")
    drum = next(item for item in result if item.target_id == "o2:unpitched:1")

    assert pitched.probabilities["piano"] > pitched.probabilities["bass"]
    assert pitched.probabilities["piano"] < 0.70
    assert drum.probabilities["drums"] > drum.probabilities["piano"]


def test_yamnet_backend_is_optional_at_import_time():
    backend = YAMNetAudioSetBackend()
    assert backend.backend_id == "yamnet-audioset:v0.1"
    assert backend._model is None


def test_audioset_frame_scores_validate_probability_range():
    with pytest.raises(ValueError):
        AudioSetFrameScores(
            onset_id="o1",
            scores={"Piano": 1.2},
        ).validate()
