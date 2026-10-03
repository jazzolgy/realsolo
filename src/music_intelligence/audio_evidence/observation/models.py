"""Model-agnostic raw observations produced by audio detectors."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Mapping


def _probabilities(values: Mapping[str, float]) -> dict[str, float]:
    if not values:
        return {}
    cleaned: dict[str, float] = {}
    for key, value in values.items():
        if not key:
            raise ValueError("probability keys may not be empty")
        value = float(value)
        if not math.isfinite(value) or value < 0.0:
            raise ValueError("probabilities must be finite and non-negative")
        cleaned[str(key)] = value
    total = sum(cleaned.values())
    if total <= 0.0:
        raise ValueError("probability mass must be positive")
    return {key: value / total for key, value in cleaned.items()}


@dataclass(frozen=True)
class DetectorEvidence:
    detector_id: str
    evidence_kind: str
    confidence: float | None = None
    detail: str | None = None

    def validate(self) -> None:
        if not self.detector_id:
            raise ValueError("detector_id is required")
        if not self.evidence_kind:
            raise ValueError("evidence_kind is required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class SeparationMetadata:
    model_id: str | None = None
    stem_label: str | None = None
    stem_confidence: float | None = None
    bleed_estimate: float | None = None

    def validate(self) -> None:
        for name in ("stem_confidence", "bleed_estimate"):
            value = getattr(self, name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


@dataclass(frozen=True)
class AudioObservation:
    """Raw detector output; not confirmed musical meaning."""

    observation_id: str
    source_id: str
    onset_seconds: float
    offset_seconds: float | None = None
    nominal_midi: float | None = None
    frequency_hz: float | None = None
    unpitched_token: str | None = None
    pitch_probabilities: Mapping[str, float] = field(default_factory=dict)
    instrument_probabilities: Mapping[str, float] = field(default_factory=dict)
    role_probabilities: Mapping[str, float] = field(default_factory=dict)
    onset_confidence: float | None = None
    duration_confidence: float | None = None
    pitch_confidence: float | None = None
    instrument_confidence: float | None = None
    dynamic: float | None = None
    spectral_centroid_hz: float | None = None
    polyphony_estimate: int | None = None
    separation: SeparationMetadata | None = None
    detector_evidence: tuple[DetectorEvidence, ...] = ()
    provenance: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.observation_id:
            raise ValueError("observation_id is required")
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.onset_seconds < 0.0:
            raise ValueError("onset_seconds may not be negative")
        if self.offset_seconds is not None and self.offset_seconds < self.onset_seconds:
            raise ValueError("offset_seconds may not precede onset_seconds")
        if self.frequency_hz is not None and self.frequency_hz <= 0.0:
            raise ValueError("frequency_hz must be positive")
        if self.nominal_midi is None and self.frequency_hz is None and not self.unpitched_token:
            raise ValueError("observation requires pitched or unpitched evidence")
        if self.unpitched_token and (self.nominal_midi is not None or self.frequency_hz is not None):
            raise ValueError("observation may not be both pitched and unpitched")
        for name in ("onset_confidence","duration_confidence","pitch_confidence","instrument_confidence","dynamic"):
            value = getattr(self, name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.spectral_centroid_hz is not None and self.spectral_centroid_hz < 0.0:
            raise ValueError("spectral_centroid_hz may not be negative")
        if self.polyphony_estimate is not None and self.polyphony_estimate < 0:
            raise ValueError("polyphony_estimate may not be negative")
        _probabilities(self.pitch_probabilities)
        _probabilities(self.instrument_probabilities)
        _probabilities(self.role_probabilities)
        if self.separation is not None:
            self.separation.validate()
        for evidence in self.detector_evidence:
            evidence.validate()

    def normalized(self) -> "AudioObservation":
        self.validate()
        return AudioObservation(**{
            **self.__dict__,
            "pitch_probabilities": _probabilities(self.pitch_probabilities),
            "instrument_probabilities": _probabilities(self.instrument_probabilities),
            "role_probabilities": _probabilities(self.role_probabilities),
            "metadata": dict(self.metadata),
        })
