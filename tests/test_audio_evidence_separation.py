from __future__ import annotations

from music_intelligence.audio_evidence import (
    SeparatedAudioEvidencePipeline,
)
from music_intelligence.audio_evidence.adapters.source import AudioSource
from music_intelligence.audio_evidence.detectors import (
    CompositeObservationDetector,
    OnsetDetection,
    PitchDetection,
    SeparatedSource,
    StemMetadataInstrumentDetector,
)
from music_intelligence.audio_evidence.observation.models import SeparationMetadata


class OneOnset:
    detector_id = "one-onset"

    def detect_onsets(self, source: AudioSource):
        return (
            OnsetDetection(
                onset_id="o1",
                onset_seconds=1.0,
                confidence=0.95,
            ),
        )


class OnePitch:
    detector_id = "one-pitch"

    def detect_pitches(self, source: AudioSource, onsets):
        return (
            PitchDetection(
                onset_id="o1",
                pitch_id="p1",
                nominal_midi=60.0,
                frequency_hz=261.63,
                confidence=0.91,
            ),
        )


class FakePianoSeparator:
    separator_id = "fake-piano-separator"

    def separate(self, source: AudioSource):
        return (
            SeparatedSource(
                source=AudioSource(
                    source_id=source.source_id + ":piano",
                    uri=source.uri,
                    start_seconds=source.start_seconds,
                    end_seconds=source.end_seconds,
                    metadata={"stem_label": "piano"},
                ),
                metadata=SeparationMetadata(
                    model_id=self.separator_id,
                    stem_label="piano",
                    stem_confidence=0.87,
                    bleed_estimate=0.12,
                ),
            ),
        )


def test_stem_metadata_detector_targets_pitch_hypothesis():
    instrument = StemMetadataInstrumentDetector()
    source = AudioSource(
        source_id="stem",
        metadata={"stem_label": "piano"},
    )
    onsets = OneOnset().detect_onsets(source)
    pitches = OnePitch().detect_pitches(source, onsets)

    result = instrument.detect_instruments(
        source,
        onsets,
        pitches,
        (),
    )

    assert len(result) == 1
    assert result[0].target_id == "p1"
    assert result[0].probabilities["piano"] > result[0].probabilities["bass"]


def test_separated_pipeline_preserves_separator_metadata_and_stem_prior():
    detector = CompositeObservationDetector(
        onset_detector=OneOnset(),
        pitch_detector=OnePitch(),
        instrument_detector=StemMetadataInstrumentDetector(),
    )
    pipeline = SeparatedAudioEvidencePipeline(
        detector=detector,
        separator=FakePianoSeparator(),
    )

    hypotheses = pipeline.analyze(
        AudioSource(source_id="mix", uri="/tmp/not-read-by-fakes.wav")
    )

    assert len(hypotheses) == 1
    hypothesis = hypotheses[0]
    assert hypothesis.observation.separation is not None
    assert hypothesis.observation.separation.stem_label == "piano"
    assert hypothesis.observation.instrument_probabilities["piano"] > 0.8
    assert hypothesis.instrument_posterior["piano"] > 0.8
    assert "audio-evidence:source-separation" in hypothesis.observation.provenance


def test_unknown_stem_label_falls_back_to_other_without_music_semantics():
    detector = StemMetadataInstrumentDetector()
    source = AudioSource(
        source_id="stem",
        metadata={"stem_label": "mystery"},
    )
    onsets = OneOnset().detect_onsets(source)
    pitches = OnePitch().detect_pitches(source, onsets)

    result = detector.detect_instruments(source, onsets, pitches, ())

    assert result[0].probabilities == {"other": 1.0}
