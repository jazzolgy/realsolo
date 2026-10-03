"""Instrument evidence derived from source-separation stem metadata.

This detector is intentionally conservative. It converts an upstream separator's
stem label into a weak instrument prior; it does not perform musical-role,
harmony, or form reasoning.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from ..adapters.source import AudioSource
from .contracts import (
    InstrumentDetection,
    OnsetDetection,
    PitchDetection,
    UnpitchedDetection,
)


def _normalize(values: Mapping[str, float]) -> dict[str, float]:
    total = sum(float(value) for value in values.values())
    if total <= 0.0:
        raise ValueError("stem prior must contain positive probability mass")
    return {str(key): float(value) / total for key, value in values.items()}


@dataclass
class StemMetadataInstrumentDetector:
    """Emit target-specific weak priors from source stem metadata."""

    detector_id: str = "stem-metadata-instrument-prior:v0.1"
    stem_priors: Mapping[str, Mapping[str, float]] = field(
        default_factory=lambda: {
            "bass": {"bass": 0.88, "piano": 0.07, "other": 0.05},
            "drums": {"drums": 0.94, "other": 0.06},
            "piano": {"piano": 0.88, "bass": 0.07, "other": 0.05},
            "other": {"other": 1.0},
        }
    )
    confidence_scale: float = 0.75

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence_scale <= 1.0:
            raise ValueError("confidence_scale must be within 0..1")

    def detect_instruments(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
        pitches: Sequence[PitchDetection] = (),
        unpitched: Sequence[UnpitchedDetection] = (),
    ) -> Sequence[InstrumentDetection]:
        stem_label = str(source.metadata.get("stem_label", "")).strip().lower()
        if not stem_label:
            return ()
        prior = self.stem_priors.get(stem_label)
        if prior is None:
            prior = self.stem_priors.get("other")
        if not prior:
            return ()

        probabilities = _normalize(prior)
        top_probability = max(probabilities.values())
        confidence = min(1.0, top_probability * self.confidence_scale)

        by_onset = {onset.onset_id for onset in onsets}
        results: list[InstrumentDetection] = []

        for pitch in pitches:
            if pitch.onset_id not in by_onset:
                continue
            results.append(
                InstrumentDetection(
                    onset_id=pitch.onset_id,
                    target_id=pitch.pitch_id,
                    probabilities=probabilities,
                    confidence=confidence,
                    detector_id=self.detector_id,
                )
            )

        unpitched_index: dict[str, int] = {}
        for token in unpitched:
            if token.onset_id not in by_onset:
                continue
            unpitched_index[token.onset_id] = unpitched_index.get(token.onset_id, 0) + 1
            target_id = token.onset_id + ":unpitched:" + str(unpitched_index[token.onset_id])
            results.append(
                InstrumentDetection(
                    onset_id=token.onset_id,
                    target_id=target_id,
                    probabilities=probabilities,
                    confidence=confidence,
                    detector_id=self.detector_id,
                )
            )

        if not pitches and not unpitched:
            for onset in onsets:
                results.append(
                    InstrumentDetection(
                        onset_id=onset.onset_id,
                        probabilities=probabilities,
                        confidence=confidence,
                        detector_id=self.detector_id,
                    )
                )

        return tuple(results)
