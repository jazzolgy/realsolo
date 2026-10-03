"""Weak instrument priors from pretrained AudioSet-style taggers.

Generic AudioSet taggers operate on coarse audio windows rather than individual
notes. Their outputs are therefore treated only as weak detector evidence and
must not be promoted directly to note ownership.
"""
from __future__ import annotations

from dataclasses import dataclass, field
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
class AudioSetFrameScores:
    onset_id: str
    scores: Mapping[str, float]

    def validate(self) -> None:
        if not self.onset_id:
            raise ValueError("onset_id is required")
        for label, score in self.scores.items():
            if not label:
                raise ValueError("tag label may not be empty")
            if not 0.0 <= float(score) <= 1.0:
                raise ValueError("tag scores must be within 0..1")


class AudioSetTagBackend(Protocol):
    backend_id: str

    def score_onsets(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
    ) -> Sequence[AudioSetFrameScores]:
        ...


DEFAULT_INSTRUMENT_TAG_MAP: Mapping[str, tuple[str, ...]] = {
    "piano": (
        "Piano",
        "Electric piano",
        "Keyboard (musical)",
    ),
    "bass": (
        "Double bass",
        "Bass guitar",
    ),
    "drums": (
        "Percussion",
        "Drum kit",
        "Drum",
        "Snare drum",
        "Bass drum",
        "Cymbal",
        "Hi-hat",
    ),
}


def _normalize(values: Mapping[str, float]) -> dict[str, float]:
    total = sum(values.values())
    if total <= 0.0:
        return {}
    return {key: value / total for key, value in values.items()}


@dataclass
class AudioSetInstrumentPriorDetector:
    backend: AudioSetTagBackend
    instrument_tag_map: Mapping[str, tuple[str, ...]] = field(
        default_factory=lambda: dict(DEFAULT_INSTRUMENT_TAG_MAP)
    )
    prior_strength: float = 0.35
    detector_id: str = "audioset-instrument-prior:v0.1"

    def __post_init__(self) -> None:
        if not 0.0 < self.prior_strength <= 1.0:
            raise ValueError("prior_strength must be within (0, 1]")

    def detect_instruments(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
        pitches: Sequence[PitchDetection] = (),
        unpitched: Sequence[UnpitchedDetection] = (),
        timbre: Sequence[TimbreDetection] = (),
    ) -> Sequence[InstrumentDetection]:
        del timbre
        frames = tuple(self.backend.score_onsets(source, onsets))
        for frame in frames:
            frame.validate()
        by_onset = {frame.onset_id: frame for frame in frames}

        output: list[InstrumentDetection] = []

        def mapped_probabilities(onset_id: str) -> dict[str, float]:
            frame = by_onset.get(onset_id)
            if frame is None:
                return {}
            mapped = {
                instrument: sum(float(frame.scores.get(tag, 0.0)) for tag in tags)
                for instrument, tags in self.instrument_tag_map.items()
            }
            mapped["other"] = max(
                0.0,
                1.0 - min(1.0, sum(mapped.values())),
            )
            normalized = _normalize(mapped)
            if not normalized:
                return {}
            uniform = 1.0 / len(normalized)
            return _normalize(
                {
                    label: (
                        self.prior_strength * probability
                        + (1.0 - self.prior_strength) * uniform
                    )
                    for label, probability in normalized.items()
                }
            )

        for pitch in pitches:
            probabilities = mapped_probabilities(pitch.onset_id)
            if not probabilities:
                continue
            ordered = sorted(probabilities.values(), reverse=True)
            output.append(
                InstrumentDetection(
                    onset_id=pitch.onset_id,
                    target_id=pitch.pitch_id,
                    probabilities=probabilities,
                    confidence=ordered[0] - ordered[1],
                    detector_id=(
                        self.detector_id + ":" + self.backend.backend_id
                    ),
                )
            )

        unpitched_index: dict[str, int] = {}
        for token in unpitched:
            probabilities = mapped_probabilities(token.onset_id)
            if not probabilities:
                continue
            unpitched_index[token.onset_id] = (
                unpitched_index.get(token.onset_id, 0) + 1
            )
            ordered = sorted(probabilities.values(), reverse=True)
            output.append(
                InstrumentDetection(
                    onset_id=token.onset_id,
                    target_id=(
                        token.onset_id
                        + ":unpitched:"
                        + str(unpitched_index[token.onset_id])
                    ),
                    probabilities=probabilities,
                    confidence=ordered[0] - ordered[1],
                    detector_id=(
                        self.detector_id + ":" + self.backend.backend_id
                    ),
                )
            )

        return tuple(output)
