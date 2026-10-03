"""Model-agnostic learned instrument-classifier boundary.

The Audio Evidence Engine owns the feature/probability transport, not a specific
ML framework. Concrete backends may use TorchScript, ONNX, a remote service, or
another implementation as long as they return calibrated class probabilities.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Mapping, Protocol, Sequence

from ..adapters.source import AudioSource
from .contracts import (
    InstrumentDetection,
    OnsetDetection,
    PitchDetection,
    TimbreDetection,
    UnpitchedDetection,
)


@dataclass(frozen=True)
class InstrumentFeatureVector:
    onset_id: str
    target_id: str
    feature_names: tuple[str, ...]
    values: tuple[float, ...]

    def validate(self) -> None:
        if not self.onset_id or not self.target_id:
            raise ValueError("onset_id and target_id are required")
        if len(self.feature_names) != len(self.values):
            raise ValueError("feature_names and values must have the same length")
        if not self.values:
            raise ValueError("feature vector may not be empty")
        if len(set(self.feature_names)) != len(self.feature_names):
            raise ValueError("feature names must be unique")
        for value in self.values:
            if not math.isfinite(value):
                raise ValueError("feature values must be finite")


class InstrumentFeatureEncoder(Protocol):
    encoder_id: str

    def encode(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
        pitches: Sequence[PitchDetection],
        unpitched: Sequence[UnpitchedDetection],
        timbre: Sequence[TimbreDetection],
    ) -> Sequence[InstrumentFeatureVector]:
        ...


class InstrumentProbabilityBackend(Protocol):
    backend_id: str

    def predict_probabilities(
        self,
        features: Sequence[InstrumentFeatureVector],
    ) -> Sequence[Mapping[str, float]]:
        ...


@dataclass
class DetectorFeatureEncoder:
    """Encode detector-side acoustic features without Core musical semantics."""

    encoder_id: str = "detector-acoustic-features:v0.1"

    def encode(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
        pitches: Sequence[PitchDetection],
        unpitched: Sequence[UnpitchedDetection],
        timbre: Sequence[TimbreDetection],
    ) -> Sequence[InstrumentFeatureVector]:
        del source
        valid_onsets = {item.onset_id for item in onsets}
        timbre_by_onset = {item.onset_id: item for item in timbre}
        output: list[InstrumentFeatureVector] = []

        for pitch in pitches:
            if pitch.onset_id not in valid_onsets:
                continue
            timbre_item = timbre_by_onset.get(pitch.onset_id)
            names = [
                "nominal_midi",
                "frequency_hz",
                "spectral_centroid_hz",
                "is_unpitched",
            ]
            values = [
                float(pitch.nominal_midi or 0.0),
                float(pitch.frequency_hz or 0.0),
                float(
                    timbre_item.spectral_centroid_hz
                    if timbre_item is not None
                    and timbre_item.spectral_centroid_hz is not None
                    else 0.0
                ),
                0.0,
            ]
            if timbre_item is not None:
                for key in sorted(timbre_item.features):
                    names.append("timbre:" + key)
                    values.append(float(timbre_item.features[key]))
            output.append(
                InstrumentFeatureVector(
                    onset_id=pitch.onset_id,
                    target_id=pitch.pitch_id,
                    feature_names=tuple(names),
                    values=tuple(values),
                )
            )

        unpitched_index: dict[str, int] = {}
        for token in unpitched:
            if token.onset_id not in valid_onsets:
                continue
            unpitched_index[token.onset_id] = (
                unpitched_index.get(token.onset_id, 0) + 1
            )
            timbre_item = timbre_by_onset.get(token.onset_id)
            names = [
                "nominal_midi",
                "frequency_hz",
                "spectral_centroid_hz",
                "is_unpitched",
            ]
            values = [
                0.0,
                0.0,
                float(
                    timbre_item.spectral_centroid_hz
                    if timbre_item is not None
                    and timbre_item.spectral_centroid_hz is not None
                    else 0.0
                ),
                1.0,
            ]
            if timbre_item is not None:
                for key in sorted(timbre_item.features):
                    names.append("timbre:" + key)
                    values.append(float(timbre_item.features[key]))
            output.append(
                InstrumentFeatureVector(
                    onset_id=token.onset_id,
                    target_id=(
                        token.onset_id
                        + ":unpitched:"
                        + str(unpitched_index[token.onset_id])
                    ),
                    feature_names=tuple(names),
                    values=tuple(values),
                )
            )

        return tuple(output)


def _normalized(probabilities: Mapping[str, float]) -> dict[str, float]:
    if not probabilities:
        raise ValueError("learned backend returned no probabilities")
    cleaned: dict[str, float] = {}
    for label, probability in probabilities.items():
        probability = float(probability)
        if not label or not math.isfinite(probability) or probability < 0.0:
            raise ValueError("invalid learned instrument probability")
        cleaned[str(label)] = probability
    total = sum(cleaned.values())
    if total <= 0.0:
        raise ValueError("learned instrument probability mass must be positive")
    return {label: value / total for label, value in cleaned.items()}


@dataclass
class LearnedInstrumentClassifier:
    """InstrumentDetector backed by an interchangeable learned predictor."""

    backend: InstrumentProbabilityBackend
    encoder: InstrumentFeatureEncoder = field(default_factory=DetectorFeatureEncoder)
    detector_id: str = "learned-instrument-classifier:v0.1"

    def detect_instruments(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
        pitches: Sequence[PitchDetection] = (),
        unpitched: Sequence[UnpitchedDetection] = (),
        timbre: Sequence[TimbreDetection] = (),
    ) -> Sequence[InstrumentDetection]:
        features = tuple(
            self.encoder.encode(
                source,
                onsets,
                pitches,
                unpitched,
                timbre,
            )
        )
        for item in features:
            item.validate()
        if not features:
            return ()

        predictions = tuple(self.backend.predict_probabilities(features))
        if len(predictions) != len(features):
            raise ValueError(
                "learned backend must return one probability distribution "
                "per feature vector"
            )

        output: list[InstrumentDetection] = []
        for feature, raw_probabilities in zip(features, predictions):
            probabilities = _normalized(raw_probabilities)
            ordered = sorted(probabilities.values(), reverse=True)
            confidence = (
                ordered[0] - ordered[1]
                if len(ordered) > 1
                else ordered[0]
            )
            output.append(
                InstrumentDetection(
                    onset_id=feature.onset_id,
                    target_id=feature.target_id,
                    probabilities=probabilities,
                    confidence=confidence,
                    detector_id=(
                        self.detector_id
                        + ":"
                        + self.backend.backend_id
                        + ":"
                        + self.encoder.encoder_id
                    ),
                )
            )

        return tuple(output)
