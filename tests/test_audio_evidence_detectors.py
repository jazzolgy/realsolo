from __future__ import annotations

from music_intelligence.audio_evidence.adapters.source import AudioSource
from music_intelligence.audio_evidence.detectors import (
    CompositeObservationDetector,
    InstrumentDetection,
    OnsetDetection,
    PitchDetection,
    TimbreDetection,
    UnpitchedDetection,
)


class FakeOnsets:
    detector_id = "fake-onsets"

    def detect_onsets(self, source: AudioSource):
        return (
            OnsetDetection(
                onset_id="o1",
                onset_seconds=1.0,
                offset_seconds=1.4,
                confidence=0.95,
            ),
        )


class FakePitches:
    detector_id = "fake-pitches"

    def detect_pitches(self, source: AudioSource, onsets):
        return (
            PitchDetection(
                onset_id="o1",
                pitch_id="p1",
                nominal_midi=60.0,
                frequency_hz=261.63,
                confidence=0.91,
                offset_seconds=1.3,
            ),
            PitchDetection(
                onset_id="o1",
                pitch_id="p2",
                nominal_midi=64.0,
                frequency_hz=329.63,
                confidence=0.88,
                offset_seconds=1.35,
            ),
        )


class FakeInstrument:
    detector_id = "fake-instrument"

    def detect_instruments(self, source: AudioSource, onsets):
        return (
            InstrumentDetection(
                onset_id="o1",
                probabilities={"piano": 0.82, "bass": 0.12, "other": 0.06},
                confidence=0.82,
                detector_id=self.detector_id,
            ),
        )


class FakeTimbre:
    detector_id = "fake-timbre"

    def detect_timbre(self, source: AudioSource, onsets):
        return (
            TimbreDetection(
                onset_id="o1",
                spectral_centroid_hz=1850.0,
                detector_id=self.detector_id,
            ),
        )


class FakeUnpitched:
    detector_id = "fake-unpitched"

    def detect_unpitched(self, source: AudioSource, onsets):
        return (
            UnpitchedDetection(
                onset_id="o1",
                token="snare",
                confidence=0.86,
            ),
        )


def test_composite_detector_preserves_polyphony_and_simultaneous_unpitched_event():
    detector = CompositeObservationDetector(
        onset_detector=FakeOnsets(),
        pitch_detector=FakePitches(),
        instrument_detector=FakeInstrument(),
        timbre_detector=FakeTimbre(),
        unpitched_detector=FakeUnpitched(),
    )

    observations = detector.detect(AudioSource(source_id="mix"))

    assert len(observations) == 3

    pitched = [item for item in observations if item.nominal_midi is not None]
    unpitched = [item for item in observations if item.unpitched_token is not None]

    assert [item.nominal_midi for item in pitched] == [60.0, 64.0]
    assert all(item.polyphony_estimate == 2 for item in pitched)
    assert all(item.instrument_probabilities["piano"] == 0.82 for item in pitched)
    assert all(item.spectral_centroid_hz == 1850.0 for item in pitched)

    assert len(unpitched) == 1
    assert unpitched[0].unpitched_token == "snare"
    assert unpitched[0].onset_seconds == 1.0


def test_composite_detector_keeps_detector_provenance():
    detector = CompositeObservationDetector(
        onset_detector=FakeOnsets(),
        pitch_detector=FakePitches(),
        instrument_detector=FakeInstrument(),
        timbre_detector=FakeTimbre(),
    )

    observation = detector.detect(AudioSource(source_id="mix"))[0]
    kinds = {item.evidence_kind for item in observation.detector_evidence}
    detector_ids = {item.detector_id for item in observation.detector_evidence}

    assert {"onset", "pitch", "instrument", "timbre"} <= kinds
    assert {
        "fake-onsets",
        "fake-pitches",
        "fake-instrument",
        "fake-timbre",
    } <= detector_ids
    assert observation.provenance == (
        "audio-evidence:composite-observation",
        "onset:o1",
    )


def test_detector_contract_does_not_assign_musical_semantics():
    detector = CompositeObservationDetector(
        onset_detector=FakeOnsets(),
        pitch_detector=FakePitches(),
        instrument_detector=FakeInstrument(),
    )

    observation = detector.detect(AudioSource(source_id="mix"))[0]

    assert observation.role_probabilities == {}
    assert "harmony" not in observation.metadata
    assert "form" not in observation.metadata
    assert "phrase" not in observation.metadata
