"""Model-independent detector contracts and raw detector outputs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol, Sequence

from ..adapters.source import AudioSource


@dataclass(frozen=True)
class OnsetDetection:
    onset_id: str
    onset_seconds: float
    confidence: float
    offset_seconds: float | None = None

    def validate(self) -> None:
        if not self.onset_id:
            raise ValueError("onset_id is required")
        if self.onset_seconds < 0.0:
            raise ValueError("onset_seconds may not be negative")
        if self.offset_seconds is not None and self.offset_seconds < self.onset_seconds:
            raise ValueError("offset_seconds may not precede onset_seconds")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("onset confidence must be within 0..1")


@dataclass(frozen=True)
class PitchDetection:
    onset_id: str
    pitch_id: str
    confidence: float
    nominal_midi: float | None = None
    frequency_hz: float | None = None
    offset_seconds: float | None = None

    def validate(self) -> None:
        if not self.onset_id or not self.pitch_id:
            raise ValueError("onset_id and pitch_id are required")
        if self.nominal_midi is None and self.frequency_hz is None:
            raise ValueError("pitch detection requires nominal_midi or frequency_hz")
        if self.frequency_hz is not None and self.frequency_hz <= 0.0:
            raise ValueError("frequency_hz must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("pitch confidence must be within 0..1")


@dataclass(frozen=True)
class UnpitchedDetection:
    onset_id: str
    token: str
    confidence: float

    def validate(self) -> None:
        if not self.onset_id or not self.token:
            raise ValueError("onset_id and token are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("unpitched confidence must be within 0..1")


@dataclass(frozen=True)
class InstrumentDetection:
    onset_id: str
    probabilities: Mapping[str, float]
    confidence: float | None = None
    detector_id: str = "instrument-detector"
    target_id: str | None = None

    def validate(self) -> None:
        if not self.onset_id:
            raise ValueError("onset_id is required")
        if not self.probabilities:
            raise ValueError("instrument probabilities are required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("instrument confidence must be within 0..1")


@dataclass(frozen=True)
class TimbreDetection:
    onset_id: str
    spectral_centroid_hz: float | None = None
    features: Mapping[str, float] = field(default_factory=dict)
    detector_id: str = "timbre-detector"

    def validate(self) -> None:
        if not self.onset_id:
            raise ValueError("onset_id is required")
        if self.spectral_centroid_hz is not None and self.spectral_centroid_hz < 0.0:
            raise ValueError("spectral_centroid_hz may not be negative")


class OnsetDetector(Protocol):
    detector_id: str

    def detect_onsets(self, source: AudioSource) -> Sequence[OnsetDetection]:
        ...


class PitchDetector(Protocol):
    detector_id: str

    def detect_pitches(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
    ) -> Sequence[PitchDetection]:
        ...


class UnpitchedDetector(Protocol):
    detector_id: str

    def detect_unpitched(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
    ) -> Sequence[UnpitchedDetection]:
        ...


class InstrumentDetector(Protocol):
    detector_id: str

    def detect_instruments(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
    ) -> Sequence[InstrumentDetection]:
        ...


class TimbreDetector(Protocol):
    detector_id: str

    def detect_timbre(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
    ) -> Sequence[TimbreDetection]:
        ...
