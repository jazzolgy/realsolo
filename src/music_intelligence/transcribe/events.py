"""Common committed-performance input contract for transcription.

This module belongs to the transcription workstream.  It normalizes already
committed / played player events into an instrument-neutral representation
without turning them into score notation.

Important boundary:
    Performance Representation != Notation Representation

No score-time quantization, enharmonic spelling, staff allocation, tie/rest
selection, or MusicXML concerns belong here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping
from fractions import Fraction


PERFORMANCE_EVIDENCE_CONTRACT_VERSION = "performance-evidence.v1"


class PerformanceCommitment(str, Enum):
    COMMITTED = "committed"
    PLAYED = "played"


def commitment_value(value: str | Enum) -> str:
    """Normalize external commitment enums without importing their package."""

    raw = getattr(value, "value", value)
    return str(raw)


class EvidenceKind(str, Enum):
    PLAYER_EVENT = "player_event"
    MIDI = "midi"
    AUDIO_ANALYSIS = "audio_analysis"
    HUMAN_ANNOTATION = "human_annotation"
    DERIVED = "derived"


@dataclass(frozen=True)
class PerformanceTimeSpan:
    """Physical/performance timing, never score-time notation."""

    onset_seconds: float
    offset_seconds: float | None = None
    transport_beat: float | None = None
    transport_offset_beat: float | None = None

    def validate(self) -> None:
        if self.onset_seconds < 0:
            raise ValueError("onset_seconds may not be negative")
        if self.offset_seconds is not None and self.offset_seconds < self.onset_seconds:
            raise ValueError("offset_seconds may not precede onset_seconds")
        if (
            self.transport_beat is not None
            and self.transport_offset_beat is not None
            and self.transport_offset_beat <= self.transport_beat
        ):
            raise ValueError("transport_offset_beat must follow transport_beat")
        if self.transport_offset_beat is not None and self.transport_beat is None:
            raise ValueError("transport_offset_beat requires transport_beat")

    @property
    def duration_seconds(self) -> float | None:
        if self.offset_seconds is None:
            return None
        return self.offset_seconds - self.onset_seconds


@dataclass(frozen=True)
class MusicalCoordinate:
    """Canonical musical location; physical time remains provenance only."""

    form: str = ""
    section: str = ""
    chorus: int | None = None
    bar_in_section: int | None = None
    beat: Fraction | None = None
    subdivision: Fraction | None = None
    confidence: float = 1.0
    uncertainty: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.chorus is not None and self.chorus < 0:
            raise ValueError("chorus may not be negative")
        if self.bar_in_section is not None and self.bar_in_section < 0:
            raise ValueError("bar_in_section may not be negative")
        if self.beat is not None and self.beat < 0:
            raise ValueError("beat may not be negative")
        if self.subdivision is not None and not 0 <= self.subdivision < 1:
            raise ValueError("subdivision must be within [0, 1)")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("musical-coordinate confidence must be within 0..1")


class DynamicChange(str, Enum):
    CRESCENDO = "crescendo"
    DECRESCENDO = "decrescendo"
    STABLE = "stable"
    ACCENT = "accent"


@dataclass(frozen=True)
class PerceptualDynamics:
    """Factorized musical dynamics, independent of source mastering level."""

    dynamic_absolute_ordinal: float | None = None
    dynamic_relative_to_track: float | None = None
    dynamic_relative_to_section: float | None = None
    dynamic_relative_to_phrase: float | None = None
    dynamic_change: DynamicChange | None = None
    dynamic_confidence: float | None = None
    dynamic_evidence: tuple[str, ...] = ()

    def validate(self) -> None:
        for name in (
            "dynamic_absolute_ordinal",
            "dynamic_relative_to_track",
            "dynamic_relative_to_section",
            "dynamic_relative_to_phrase",
            "dynamic_confidence",
        ):
            value = getattr(self, name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


@dataclass(frozen=True)
class PerformedPitch:
    """Performed pitch evidence without collapsing pitch to one MIDI integer."""

    nominal_midi: float | None = None
    frequency_hz: float | None = None
    cents_offset: float | None = None
    continuous_pitch_ref: str | None = None

    def validate(self) -> None:
        if self.nominal_midi is None and self.frequency_hz is None and not self.continuous_pitch_ref:
            raise ValueError(
                "performed pitch requires nominal_midi, frequency_hz, or continuous_pitch_ref"
            )
        if self.frequency_hz is not None and self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be positive")


@dataclass(frozen=True)
class UnpitchedToken:
    """Instrument-neutral identity for unpitched/percussive events."""

    token: str
    instrument_family: str | None = None
    technique: str | None = None

    def validate(self) -> None:
        if not self.token:
            raise ValueError("unpitched token is required")


@dataclass(frozen=True)
class ConfidenceBundle:
    """Keep uncertainty factorized instead of flattening it to one score."""

    pitch: float | None = None
    rhythm: float | None = None
    instrument: float | None = None
    voice: float | None = None
    articulation: float | None = None
    ornament: float | None = None
    notation_relevance: float | None = None
    overall_source: float | None = None

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} confidence must be within 0..1")


@dataclass(frozen=True)
class EvidenceRef:
    kind: EvidenceKind
    source_id: str
    detail: str | None = None
    confidence: float | None = None

    def validate(self) -> None:
        if not self.source_id:
            raise ValueError("evidence source_id is required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("evidence confidence must be within 0..1")


@dataclass(frozen=True)
class EventAlternative:
    """A preserved alternative interpretation of one performance attribute."""

    attribute: str
    value: str
    confidence: float | None = None
    evidence_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.attribute:
            raise ValueError("alternative attribute is required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("alternative confidence must be within 0..1")


@dataclass(frozen=True)
class CommittedPerformanceEvent:
    """Common transcription intake schema for player/audio performance evidence.

    The event describes what was performed and any semantics already known by
    Shared Core / the originating player.  It intentionally does not prescribe
    how the event will be written in a score.
    """

    event_id: str
    player_id: str
    instrument: str
    commitment: PerformanceCommitment | str | Enum
    time: PerformanceTimeSpan

    pitch: PerformedPitch | None = None
    unpitched: UnpitchedToken | None = None

    voice_role: str | None = None
    layer_role: str | None = None
    dynamic: float | None = None
    musical_coordinate: MusicalCoordinate | None = None
    dynamics: PerceptualDynamics | None = None
    articulation: tuple[str, ...] = ()
    ornament: tuple[str, ...] = ()
    technique: tuple[str, ...] = ()

    gesture_id: str | None = None
    harmonic_context_id: str | None = None
    phrase_context_id: str | None = None
    ensemble_state_id: str | None = None

    confidence: ConfidenceBundle = field(default_factory=ConfidenceBundle)
    alternatives: tuple[EventAlternative, ...] = ()
    evidence: tuple[EvidenceRef, ...] = ()
    provenance: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.event_id:
            raise ValueError("event_id is required")
        if not self.player_id:
            raise ValueError("player_id is required")
        if not self.instrument:
            raise ValueError("instrument is required")
        if commitment_value(self.commitment) not in {
            PerformanceCommitment.COMMITTED.value,
            PerformanceCommitment.PLAYED.value,
        }:
            raise ValueError("transcription accepts only committed or played events")

        self.time.validate()
        self.confidence.validate()
        if self.musical_coordinate is not None:
            self.musical_coordinate.validate()
        if self.dynamics is not None:
            self.dynamics.validate()

        if self.pitch is not None and self.unpitched is not None:
            raise ValueError("event may be pitched or unpitched, not both")
        if self.pitch is None and self.unpitched is None:
            raise ValueError("event requires pitch or unpitched token")

        if self.pitch is not None:
            self.pitch.validate()
        if self.unpitched is not None:
            self.unpitched.validate()

        if self.dynamic is not None and not 0.0 <= self.dynamic <= 1.0:
            raise ValueError("dynamic must be within 0..1")

        for alt in self.alternatives:
            alt.validate()
        for ref in self.evidence:
            ref.validate()

    @property
    def duration_seconds(self) -> float | None:
        return self.time.duration_seconds
