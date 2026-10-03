from __future__ import annotations

from music_intelligence.audio_evidence import (
    AudioEvidencePipeline,
    AudioObservation,
    AudioSource,
    BoundedContextPosterior,
    ContextEvidence,
    RevisionLedger,
    confidence_report,
    to_performance_evidence_payload,
)


def ambiguous_f3() -> AudioObservation:
    return AudioObservation(
        observation_id="synthetic:f3:001",
        source_id="synthetic-source",
        onset_seconds=1.25,
        offset_seconds=1.66,
        nominal_midi=53.0,
        frequency_hz=174.61,
        instrument_probabilities={
            "bass": 0.48,
            "piano_lh": 0.46,
            "other": 0.06,
        },
        role_probabilities={
            "time_floor": 0.55,
            "harmonic_support": 0.45,
        },
        pitch_confidence=0.91,
        onset_confidence=0.96,
        duration_confidence=0.67,
        instrument_confidence=0.48,
        provenance=("test:raw-detector",),
    )


def test_raw_observation_is_preserved_separately_from_context_posterior():
    raw = ambiguous_f3()
    hypothesis = BoundedContextPosterior(max_context_log_shift=1.0).revise_instrument(
        raw,
        (
            ContextEvidence(
                factor_id="continuity",
                likelihoods={"bass": 1000.0, "piano_lh": 0.001, "other": 0.001},
                weight=1.0,
            ),
        ),
    )

    assert hypothesis.observation.instrument_probabilities["bass"] == 0.48
    assert hypothesis.instrument_posterior["bass"] > 0.48
    assert hypothesis.instrument_posterior["bass"] < 0.90
    assert hypothesis.revision is not None
    assert hypothesis.revision.factor_ids == ("continuity",)


def test_confidence_report_does_not_collapse_raw_and_posterior_confidence():
    raw = ambiguous_f3()
    hypothesis = BoundedContextPosterior().revise_instrument(
        raw,
        (
            ContextEvidence(
                factor_id="low-register-continuity",
                likelihoods={"bass": 2.0, "piano_lh": 0.8, "other": 0.5},
                weight=0.7,
            ),
        ),
    )
    report = confidence_report(hypothesis)

    assert report.raw_instrument_confidence == 0.48
    assert report.posterior_top_probability is not None
    assert report.posterior_margin is not None
    assert report.posterior_entropy is not None
    assert report.pitch_confidence == 0.91


def test_ambiguous_hypothesis_is_not_forced_into_performance_evidence():
    hypothesis = BoundedContextPosterior().revise_instrument(ambiguous_f3())

    assert (
        to_performance_evidence_payload(
            hypothesis,
            player_id="audio-player:unknown",
        )
        is None
    )


def test_resolved_hypothesis_projects_to_versioned_performance_evidence_payload():
    raw = AudioObservation(
        observation_id="synthetic:c4:001",
        source_id="synthetic-source",
        onset_seconds=2.0,
        offset_seconds=2.5,
        nominal_midi=60.0,
        frequency_hz=261.63,
        instrument_probabilities={"piano": 0.84, "bass": 0.10, "other": 0.06},
        role_probabilities={"foreground_line": 0.70, "harmonic_support": 0.30},
        pitch_confidence=0.94,
        onset_confidence=0.97,
        duration_confidence=0.81,
        instrument_confidence=0.84,
        dynamic=0.62,
        provenance=("test:pitch-model",),
    )
    hypothesis = BoundedContextPosterior().revise_instrument(
        raw,
        (
            ContextEvidence(
                factor_id="stem-piano",
                likelihoods={"piano": 2.0, "bass": 0.6, "other": 0.7},
                weight=0.5,
            ),
        ),
    )

    payload = to_performance_evidence_payload(
        hypothesis,
        player_id="audio-player:piano",
    )

    assert payload is not None
    assert payload["schema_version"] == "performance-evidence.v1"
    assert payload["commitment"] == "played"
    assert payload["instrument"] == "piano"
    assert payload["pitch"]["nominal_midi"] == 60.0
    assert payload["layer_role"] == "foreground_line"
    assert payload["confidence"]["pitch"] == 0.94
    assert payload["confidence"]["overall_source"] == 0.84
    assert payload["alternatives"]
    assert payload["evidence"][0]["detail"] == "raw_observation:synthetic:c4:001"
    assert payload["raw_instrument_probabilities"][0]["label"] == "piano"
    assert payload["context_instrument_probabilities"][0]["label"] == "piano"
    assert payload["raw_confidence"]["instrument"] == 0.84
    assert payload["contextual_confidence"]["instrument"] is not None
    assert payload["context_corrections"][0]["source_ref"] == "audio-context"
    assert payload["revision_history"][0]["attribute"] == "instrument_distribution"
    assert "posterior_margin" in payload["metadata"]
    assert "posterior_entropy" in payload["metadata"]


def test_unpitched_observation_projects_without_pitch():
    raw = AudioObservation(
        observation_id="synthetic:snare:001",
        source_id="synthetic-source",
        onset_seconds=3.0,
        offset_seconds=3.08,
        unpitched_token="snare",
        instrument_probabilities={"drums": 0.92, "other": 0.08},
        onset_confidence=0.98,
        instrument_confidence=0.92,
    )
    hypothesis = BoundedContextPosterior().revise_instrument(raw)
    payload = to_performance_evidence_payload(
        hypothesis,
        player_id="audio-player:drums",
    )

    assert payload is not None
    assert payload["pitch"] is None
    assert payload["unpitched"]["token"] == "snare"
    assert payload["unpitched"]["instrument_family"] == "drums"


class FakeDetector:
    detector_id = "fake-detector"

    def detect(self, source: AudioSource):
        assert source.source_id == "unit-source"
        return (ambiguous_f3(),)


def test_pipeline_keeps_detector_and_context_stages_replaceable():
    pipeline = AudioEvidencePipeline(
        detector=FakeDetector(),
        context_provider=lambda observation: (
            ContextEvidence(
                factor_id="register-continuity",
                likelihoods={"bass": 1.8, "piano_lh": 0.9, "other": 0.6},
                weight=0.5,
            ),
        ),
    )

    result = pipeline.analyze(AudioSource(source_id="unit-source"))

    assert len(result) == 1
    assert result[0].observation.observation_id == "synthetic:f3:001"
    assert result[0].revision is not None
    assert result[0].revision.factor_ids == ("register-continuity",)


def test_revision_ledger_preserves_history_and_collects_hard_examples():
    raw = ambiguous_f3()
    posterior = BoundedContextPosterior()
    first = posterior.revise_instrument(raw)
    second = posterior.revise_instrument(
        raw,
        (
            ContextEvidence(
                factor_id="weak-continuity",
                likelihoods={"bass": 1.1, "piano_lh": 1.0, "other": 0.9},
                weight=0.3,
            ),
        ),
    )

    ledger = RevisionLedger()
    first_record = ledger.record(first)
    second_record = ledger.record(second)

    assert first_record.revision_index == 1
    assert second_record.revision_index == 2
    assert len(ledger.history_for(raw.observation_id)) == 2
    assert ledger.hard_examples
    assert ledger.hard_examples[-1].observation_id == raw.observation_id
