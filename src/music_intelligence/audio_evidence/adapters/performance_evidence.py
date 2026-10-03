"""Projection boundary into Performance Evidence.

This module deliberately does not import the Transcription/Notation package.
That contract is owned by a separate development stream. The adapter emits a
versioned payload compatible with performance-evidence.v1.
"""
from __future__ import annotations

from typing import Any

from ..calibration.confidence import confidence_report
from ..posterior.fusion import ContextualAudioHypothesis

PERFORMANCE_EVIDENCE_VERSION = "performance-evidence.v1"


def _rank(probabilities: Any) -> list[tuple[str, float]]:
    return sorted(
        dict(probabilities).items(),
        key=lambda item: item[1],
        reverse=True,
    )


def to_performance_evidence_payload(
    hypothesis: ContextualAudioHypothesis,
    *,
    player_id: str,
    minimum_instrument_probability: float = 0.70,
    minimum_instrument_margin: float = 0.15,
) -> dict[str, Any] | None:
    """Project only sufficiently resolved hypotheses to committed evidence.

    Ambiguous hypotheses stay inside Audio Evidence Engine. They are not forced
    into a scalar instrument assignment merely to satisfy the downstream
    contract.
    """

    observation = hypothesis.observation
    observation.validate()
    if not player_id:
        raise ValueError("player_id is required")

    ranking = _rank(hypothesis.instrument_posterior)
    if not ranking:
        return None

    top_instrument, top_probability = ranking[0]
    runner_up = ranking[1][1] if len(ranking) > 1 else 0.0
    if (
        top_probability < minimum_instrument_probability
        or top_probability - runner_up < minimum_instrument_margin
    ):
        return None

    report = confidence_report(hypothesis)

    alternatives = [
        {
            "attribute": "instrument",
            "value": instrument,
            "confidence": probability,
            "evidence_ids": [observation.observation_id],
        }
        for instrument, probability in ranking[1:]
    ]

    evidence = [
        {
            "kind": "audio_analysis",
            "source_id": observation.source_id,
            "detail": "raw_observation:" + observation.observation_id,
            "confidence": observation.instrument_confidence,
        }
    ]

    if hypothesis.revision is not None:
        evidence.append(
            {
                "kind": "derived",
                "source_id": observation.source_id,
                "detail": "context_posterior:"
                + ",".join(hypothesis.revision.factor_ids),
                "confidence": report.posterior_top_probability,
            }
        )

    if observation.unpitched_token:
        pitch = None
        unpitched = {
            "token": observation.unpitched_token,
            "instrument_family": top_instrument,
            "technique": None,
        }
    else:
        pitch = {
            "nominal_midi": observation.nominal_midi,
            "frequency_hz": observation.frequency_hz,
            "cents_offset": None,
            "continuous_pitch_ref": None,
        }
        unpitched = None

    metadata = dict(observation.metadata)
    metadata.update(
        {
            "audio_observation_id": observation.observation_id,
            "raw_instrument_probabilities": repr(
                dict(observation.instrument_probabilities)
            ),
            "posterior_instrument_probabilities": repr(
                dict(hypothesis.instrument_posterior)
            ),
            "posterior_margin": (
                ""
                if report.posterior_margin is None
                else f"{report.posterior_margin:.6f}"
            ),
            "posterior_entropy": (
                ""
                if report.posterior_entropy is None
                else f"{report.posterior_entropy:.6f}"
            ),
        }
    )

    layer_role = None
    if hypothesis.role_posterior:
        layer_role = max(
            hypothesis.role_posterior,
            key=hypothesis.role_posterior.get,
        )

    provenance = list(observation.provenance)
    if hypothesis.revision is not None:
        provenance.extend(hypothesis.revision.provenance)
    provenance.append("audio-evidence:performance-evidence-projection")

    return {
        "schema_version": PERFORMANCE_EVIDENCE_VERSION,
        "event_id": "audio:" + observation.observation_id,
        "player_id": player_id,
        "instrument": top_instrument,
        "commitment": "played",
        "time": {
            "onset_seconds": observation.onset_seconds,
            "offset_seconds": observation.offset_seconds,
            "transport_beat": None,
            "transport_offset_beat": None,
        },
        "pitch": pitch,
        "unpitched": unpitched,
        "voice_role": None,
        "layer_role": layer_role,
        "dynamic": observation.dynamic,
        "articulation": [],
        "ornament": [],
        "technique": [],
        "gesture_id": None,
        "harmonic_context_id": None,
        "phrase_context_id": None,
        "ensemble_state_id": None,
        "confidence": {
            "pitch": report.pitch_confidence,
            "rhythm": report.onset_confidence,
            "instrument": report.posterior_top_probability,
            "voice": None,
            "articulation": None,
            "ornament": None,
            "notation_relevance": None,
            "overall_source": observation.instrument_confidence,
        },
        "alternatives": alternatives,
        "evidence": evidence,
        "provenance": provenance,
        "metadata": metadata,
    }
