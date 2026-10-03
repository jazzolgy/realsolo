"""Common committed-performance input contract for transcription.

Performance Representation != Notation Representation.

This module is deliberately source-neutral. It may accept enum-like values from
RealSolo or a future standalone application, but it does not import those
packages. No score-time quantization, spelling, staff allocation, engraving, or
renderer concerns belong here.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping

CONTRACT_VERSION = "performance-evidence.v1"


class PerformanceCommitment(str, Enum):
    COMMITTED = "committed"
    PLAYED = "played"


def commitment_value(value: str | Enum) -> str:
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
class PerformedPitch:
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
    token: str
    instrument_family: str | None = None
    technique: str | None = None

    def validate(self) -> None:
        if not self.token:
            raise ValueError("unpitched token is required")


@dataclass(frozen=True)
class ConfidenceBundle:
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
class ProbabilityEstimate:
    """Named categorical probability preserved at one inference stage."""

    label: str
    probability: float

    def validate(self) -> None:
        if not self.label:
            raise ValueError("probability label is required")
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must be within 0..1")


@dataclass(frozen=True)
class ContextCorrection:
    """One auditable reason why context changed an observation."""

    reason: str
    source_ref: str | None = None
    weight: float | None = None

    def validate(self) -> None:
        if not self.reason:
            raise ValueError("context correction reason is required")
        if self.weight is not None and not 0.0 <= self.weight <= 1.0:
            raise ValueError("context correction weight must be within 0..1")


@dataclass(frozen=True)
class EvidenceRevision:
    """Immutable audit record for a changed interpretation."""

    revision_id: str
    attribute: str
    prior_value: str | None = None
    revised_value: str | None = None
    reason: str | None = None
    source_ref: str | None = None

    def validate(self) -> None:
        if not self.revision_id:
            raise ValueError("revision_id is required")
        if not self.attribute:
            raise ValueError("revision attribute is required")


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
    articulation: tuple[str, ...] = ()
    ornament: tuple[str, ...] = ()
    technique: tuple[str, ...] = ()

    gesture_id: str | None = None
    harmonic_context_id: str | None = None
    phrase_context_id: str | None = None
    ensemble_state_id: str | None = None

    confidence: ConfidenceBundle = field(default_factory=ConfidenceBundle)

    # Observation and interpretation are deliberately separate. Raw detector
    # output is never overwritten by contextual inference.
    raw_instrument_probabilities: tuple[ProbabilityEstimate, ...] = ()
    context_instrument_probabilities: tuple[ProbabilityEstimate, ...] = ()
    raw_role_probabilities: tuple[ProbabilityEstimate, ...] = ()
    context_role_probabilities: tuple[ProbabilityEstimate, ...] = ()
    raw_confidence: ConfidenceBundle | None = None
    contextual_confidence: ConfidenceBundle | None = None
    context_corrections: tuple[ContextCorrection, ...] = ()
    revision_history: tuple[EvidenceRevision, ...] = ()

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
        if self.raw_confidence is not None:
            self.raw_confidence.validate()
        if self.contextual_confidence is not None:
            self.contextual_confidence.validate()

        for distribution_name, distribution in (
            ("raw_instrument_probabilities", self.raw_instrument_probabilities),
            ("context_instrument_probabilities", self.context_instrument_probabilities),
            ("raw_role_probabilities", self.raw_role_probabilities),
            ("context_role_probabilities", self.context_role_probabilities),
        ):
            for item in distribution:
                item.validate()
            total = sum(item.probability for item in distribution)
            if distribution and total > 1.000001:
                raise ValueError(f"{distribution_name} probabilities may not sum above 1")

        for correction in self.context_corrections:
            correction.validate()
        for revision in self.revision_history:
            revision.validate()

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


def event_to_payload(event: CommittedPerformanceEvent) -> dict[str, Any]:
    """Serialize the public contract without importing an application model."""

    event.validate()
    payload = asdict(event)
    payload["schema_version"] = CONTRACT_VERSION
    payload["commitment"] = commitment_value(event.commitment)
    if event.evidence:
        payload["evidence"] = [
            {
                **asdict(ref),
                "kind": ref.kind.value,
            }
            for ref in event.evidence
        ]
    payload["raw_instrument_probabilities"] = [
        asdict(item) for item in event.raw_instrument_probabilities
    ]
    payload["context_instrument_probabilities"] = [
        asdict(item) for item in event.context_instrument_probabilities
    ]
    payload["raw_role_probabilities"] = [
        asdict(item) for item in event.raw_role_probabilities
    ]
    payload["context_role_probabilities"] = [
        asdict(item) for item in event.context_role_probabilities
    ]
    payload["context_corrections"] = [asdict(item) for item in event.context_corrections]
    payload["revision_history"] = [asdict(item) for item in event.revision_history]
    payload["articulation"] = list(event.articulation)
    payload["ornament"] = list(event.ornament)
    payload["technique"] = list(event.technique)
    payload["alternatives"] = [
        {
            **asdict(alt),
            "evidence_ids": list(alt.evidence_ids),
        }
        for alt in event.alternatives
    ]
    payload["provenance"] = list(event.provenance)
    payload["metadata"] = dict(event.metadata)
    return payload


def event_from_payload(payload: Mapping[str, Any]) -> CommittedPerformanceEvent:
    """Deserialize v1 Performance Evidence.

    Unknown future schema versions are rejected rather than silently misread.
    """

    version = str(payload.get("schema_version", CONTRACT_VERSION))
    if version != CONTRACT_VERSION:
        raise ValueError(f"unsupported performance evidence schema: {version}")

    pitch_raw = payload.get("pitch")
    unpitched_raw = payload.get("unpitched")
    confidence_raw = payload.get("confidence") or {}
    alternatives_raw = payload.get("alternatives") or ()
    evidence_raw = payload.get("evidence") or ()

    event = CommittedPerformanceEvent(
        event_id=str(payload["event_id"]),
        player_id=str(payload["player_id"]),
        instrument=str(payload["instrument"]),
        commitment=str(payload["commitment"]),
        time=PerformanceTimeSpan(**dict(payload["time"])),
        pitch=PerformedPitch(**dict(pitch_raw)) if pitch_raw else None,
        unpitched=UnpitchedToken(**dict(unpitched_raw)) if unpitched_raw else None,
        voice_role=payload.get("voice_role"),
        layer_role=payload.get("layer_role"),
        dynamic=payload.get("dynamic"),
        articulation=tuple(payload.get("articulation") or ()),
        ornament=tuple(payload.get("ornament") or ()),
        technique=tuple(payload.get("technique") or ()),
        gesture_id=payload.get("gesture_id"),
        harmonic_context_id=payload.get("harmonic_context_id"),
        phrase_context_id=payload.get("phrase_context_id"),
        ensemble_state_id=payload.get("ensemble_state_id"),
        confidence=ConfidenceBundle(**dict(confidence_raw)),
        raw_instrument_probabilities=tuple(
            ProbabilityEstimate(**dict(item))
            for item in payload.get("raw_instrument_probabilities") or ()
        ),
        context_instrument_probabilities=tuple(
            ProbabilityEstimate(**dict(item))
            for item in payload.get("context_instrument_probabilities") or ()
        ),
        raw_role_probabilities=tuple(
            ProbabilityEstimate(**dict(item))
            for item in payload.get("raw_role_probabilities") or ()
        ),
        context_role_probabilities=tuple(
            ProbabilityEstimate(**dict(item))
            for item in payload.get("context_role_probabilities") or ()
        ),
        raw_confidence=(
            ConfidenceBundle(**dict(payload["raw_confidence"]))
            if payload.get("raw_confidence")
            else None
        ),
        contextual_confidence=(
            ConfidenceBundle(**dict(payload["contextual_confidence"]))
            if payload.get("contextual_confidence")
            else None
        ),
        context_corrections=tuple(
            ContextCorrection(**dict(item))
            for item in payload.get("context_corrections") or ()
        ),
        revision_history=tuple(
            EvidenceRevision(**dict(item))
            for item in payload.get("revision_history") or ()
        ),
        alternatives=tuple(
            EventAlternative(
                attribute=str(item["attribute"]),
                value=str(item["value"]),
                confidence=item.get("confidence"),
                evidence_ids=tuple(item.get("evidence_ids") or ()),
            )
            for item in alternatives_raw
        ),
        evidence=tuple(
            EvidenceRef(
                kind=EvidenceKind(str(item["kind"])),
                source_id=str(item["source_id"]),
                detail=item.get("detail"),
                confidence=item.get("confidence"),
            )
            for item in evidence_raw
        ),
        provenance=tuple(payload.get("provenance") or ()),
        metadata=dict(payload.get("metadata") or {}),
    )
    event.validate()
    return event
