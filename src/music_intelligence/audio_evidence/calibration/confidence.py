"""Confidence summaries without collapsing raw and posterior uncertainty."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from ..posterior.fusion import ContextualAudioHypothesis


def _entropy(probabilities: Mapping[str, float]) -> float | None:
    if not probabilities:
        return None
    n = len(probabilities)
    if n <= 1:
        return 0.0
    raw = -sum(
        probability * math.log(max(probability, 1e-12))
        for probability in probabilities.values()
    )
    return raw / math.log(n)


def _margin(probabilities: Mapping[str, float]) -> float | None:
    if not probabilities:
        return None
    ordered = sorted(probabilities.values(), reverse=True)
    return ordered[0] if len(ordered) == 1 else ordered[0] - ordered[1]


@dataclass(frozen=True)
class ConfidenceReport:
    raw_instrument_confidence: float | None
    posterior_top_probability: float | None
    posterior_margin: float | None
    posterior_entropy: float | None
    pitch_confidence: float | None
    onset_confidence: float | None
    duration_confidence: float | None


def confidence_report(
    hypothesis: ContextualAudioHypothesis,
) -> ConfidenceReport:
    posterior = hypothesis.instrument_posterior
    return ConfidenceReport(
        raw_instrument_confidence=hypothesis.observation.instrument_confidence,
        posterior_top_probability=max(posterior.values()) if posterior else None,
        posterior_margin=_margin(posterior),
        posterior_entropy=_entropy(posterior),
        pitch_confidence=hypothesis.observation.pitch_confidence,
        onset_confidence=hypothesis.observation.onset_confidence,
        duration_confidence=hypothesis.observation.duration_confidence,
    )
