"""Uncertainty-preserving evidence contracts for Shared Audio Intelligence."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from math import isfinite
from typing import Mapping


class EventStatus(str, Enum):
    NOTE_HYPOTHESIS = "note_hypothesis"
    EVENT_HYPOTHESIS = "event_hypothesis"
    ATTRIBUTION_REVISED = "attribution_revised"
    CONFIRMED = "confirmed"


def _probabilities(values: Mapping[str, float], *, field_name: str) -> dict[str, float]:
    out = {str(k): float(v) for k, v in values.items() if str(k)}
    if not out:
        return {}
    if any((not isfinite(v)) or v < 0.0 for v in out.values()):
        raise ValueError(f"{field_name} values must be finite and non-negative")
    total = sum(out.values())
    if total <= 0.0:
        raise ValueError(f"{field_name} must contain positive mass")
    return {k: v / total for k, v in out.items()}


@dataclass(frozen=True)
class ConfidenceVector:
    pitch: float | None = None
    onset: float | None = None
    duration: float | None = None
    instrument: float | None = None
    alignment: float | None = None
    role: float | None = None

    def validate(self) -> None:
        for name, value in self.as_dict().items():
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} confidence must be within 0..1")

    def as_dict(self) -> dict[str, float | None]:
        return {
            "pitch": self.pitch,
            "onset": self.onset,
            "duration": self.duration,
            "instrument": self.instrument,
            "alignment": self.alignment,
            "role": self.role,
        }


@dataclass(frozen=True)
class AudioEventHypothesis:
    event_id: str
    source_id: str
    onset_time: float
    duration: float
    pitch_midi: float | None = None
    unpitched_token: str = ""
    beat_position: float | None = None
    bar_index: int | None = None
    beat_in_bar: float | None = None
    duration_beats: float | None = None
    instrument_probabilities: Mapping[str, float] = field(default_factory=dict)
    role_probabilities: Mapping[str, float] = field(default_factory=dict)
    dynamic: float | None = None
    accent: float = 0.5
    articulation: tuple[str, ...] = ()
    timing_offset_beats: float = 0.0
    polyphony_context: Mapping[str, object] = field(default_factory=dict)
    harmony_context: str = ""
    phrase_id: str = ""
    confidence: ConfidenceVector = field(default_factory=ConfidenceVector)
    provenance: tuple[str, ...] = ()
    status: EventStatus = EventStatus.NOTE_HYPOTHESIS

    def validate(self) -> None:
        if not self.event_id or not self.source_id:
            raise ValueError("event_id and source_id are required")
        if self.onset_time < 0.0 or self.duration <= 0.0:
            raise ValueError("onset_time must be non-negative and duration positive")
        if self.pitch_midi is None and not self.unpitched_token:
            raise ValueError("event requires pitch_midi or unpitched_token")
        if self.pitch_midi is not None and not 0.0 <= self.pitch_midi <= 127.0:
            raise ValueError("pitch_midi must be within 0..127")
        if self.beat_position is not None and self.beat_position < 0.0:
            raise ValueError("beat_position cannot be negative")
        if self.bar_index is not None and self.bar_index < 1:
            raise ValueError("bar_index must be 1-based")
        if self.beat_in_bar is not None and self.beat_in_bar < 0.0:
            raise ValueError("beat_in_bar cannot be negative")
        if self.duration_beats is not None and self.duration_beats <= 0.0:
            raise ValueError("duration_beats must be positive")
        if self.dynamic is not None and not 0.0 <= self.dynamic <= 1.0:
            raise ValueError("dynamic must be within 0..1")
        if not 0.0 <= self.accent <= 1.0:
            raise ValueError("accent must be within 0..1")
        _probabilities(self.instrument_probabilities, field_name="instrument_probabilities")
        _probabilities(self.role_probabilities, field_name="role_probabilities")
        self.confidence.validate()

    def normalized(self) -> "AudioEventHypothesis":
        self.validate()
        return replace(
            self,
            instrument_probabilities=_probabilities(
                self.instrument_probabilities,
                field_name="instrument_probabilities",
            ),
            role_probabilities=_probabilities(
                self.role_probabilities,
                field_name="role_probabilities",
            ),
        )


@dataclass(frozen=True)
class AttributionFactor:
    factor: str
    likelihoods: Mapping[str, float]
    weight: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.factor:
            raise ValueError("factor is required")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("weight must be within 0..1")
        _probabilities(self.likelihoods, field_name="likelihoods")

    def normalized_likelihoods(self) -> dict[str, float]:
        self.validate()
        return _probabilities(self.likelihoods, field_name="likelihoods")


@dataclass(frozen=True)
class RevisionRecord:
    event_id: str
    revision_index: int
    previous_probabilities: Mapping[str, float]
    revised_probabilities: Mapping[str, float]
    factors: tuple[str, ...]
    reason: str
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class AttributionRevision:
    event: AudioEventHypothesis
    record: RevisionRecord
    top_instrument: str
    top_probability: float
    runner_up_probability: float

    @property
    def margin(self) -> float:
        return self.top_probability - self.runner_up_probability

    @property
    def ambiguous(self) -> bool:
        return self.margin < 0.15 or self.top_probability < 0.70
