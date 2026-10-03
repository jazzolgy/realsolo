from __future__ import annotations

from music_intelligence.audio_evidence.adapters.source import AudioSource
from music_intelligence.audio_evidence.detectors import (
    AcousticInstrumentPriorDetector,
    OnsetDetection,
    PitchDetection,
    TimbreDetection,
    UnpitchedDetection,
)


def test_low_register_acoustic_prior_remains_bass_piano_ambiguous():
    detector = AcousticInstrumentPriorDetector()
    onsets = (
        OnsetDetection(onset_id="o1", onset_seconds=1.0, confidence=0.9),
    )
    pitches = (
        PitchDetection(
            onset_id="o1",
            pitch_id="p1",
            nominal_midi=48.0,
            frequency_hz=130.81,
            confidence=0.9,
        ),
    )
    timbre = (
        TimbreDetection(
            onset_id="o1",
            spectral_centroid_hz=1100.0,
        ),
    )

    result = detector.detect_instruments(
        AudioSource(source_id="mix"),
        onsets,
        pitches,
        (),
        timbre,
    )[0]

    assert result.target_id == "p1"
    assert result.probabilities["bass"] > 0.40
    assert result.probabilities["piano"] > 0.35
    assert result.confidence < 0.10


def test_high_register_acoustic_prior_favors_piano_without_core_reasoning():
    detector = AcousticInstrumentPriorDetector()
    onsets = (
        OnsetDetection(onset_id="o1", onset_seconds=1.0, confidence=0.9),
    )
    pitches = (
        PitchDetection(
            onset_id="o1",
            pitch_id="p1",
            nominal_midi=72.0,
            frequency_hz=523.25,
            confidence=0.9,
        ),
    )
    timbre = (
        TimbreDetection(
            onset_id="o1",
            spectral_centroid_hz=2600.0,
        ),
    )

    result = detector.detect_instruments(
        AudioSource(source_id="mix"),
        onsets,
        pitches,
        (),
        timbre,
    )[0]

    assert result.probabilities["piano"] > 0.85
    assert result.probabilities["bass"] < 0.08


def test_unpitched_acoustic_prior_targets_drums():
    detector = AcousticInstrumentPriorDetector()
    onsets = (
        OnsetDetection(onset_id="o1", onset_seconds=1.0, confidence=0.9),
    )
    unpitched = (
        UnpitchedDetection(onset_id="o1", token="snare", confidence=0.8),
    )

    result = detector.detect_instruments(
        AudioSource(source_id="mix"),
        onsets,
        (),
        unpitched,
        (),
    )[0]

    assert result.target_id == "o1:unpitched:1"
    assert result.probabilities["drums"] == 0.88
