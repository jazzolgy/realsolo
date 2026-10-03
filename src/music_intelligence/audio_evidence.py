"""Canonical Audio Evidence contracts and aggregate-learning facade.

This module is the Shared Core boundary for listener/detector evidence.
Raw detector output, context-corrected posterior and optional canonical musical
position stay separate. Physical/source seconds are provenance, never the
musical identity.

The older aggregate learning adapter remains implemented in
music_intelligence.learning.audio_evidence and is re-exported here; there is no
second aggregate engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import log2
from typing import Mapping

from music_intelligence.learning.audio_evidence import artifacts_from_audio_aggregate
from music_intelligence.learning.representation import StructuralPerformanceEvent
from music_intelligence.learning.score_alignment import MusicalScoreCoordinate


def _validate_probability_map(values: Mapping[str,float], name: str) -> None:
    total=0.0
    for key,value in values.items():
        if not key or not 0.0 <= float(value) <= 1.0:
            raise ValueError(f"{name} values must be named probabilities within 0..1")
        total += float(value)
    if values and total > 1.000001:
        raise ValueError(f"{name} probabilities may not sum above 1")


@dataclass(frozen=True)
class DetectorEvidence:
    """What the detector heard before musical-context correction."""

    instrument_probabilities: Mapping[str,float] = field(default_factory=dict)
    role_probabilities: Mapping[str,float] = field(default_factory=dict)
    confidence_fields: Mapping[str,float] = field(default_factory=dict)
    pitch_hz: float | None = None
    onset: bool = False
    onset_strength: float | None = None
    rms: float | None = None

    def validate(self) -> None:
        _validate_probability_map(self.instrument_probabilities,"instrument_probabilities")
        _validate_probability_map(self.role_probabilities,"role_probabilities")
        for key,value in self.confidence_fields.items():
            if not key or not 0.0 <= float(value) <= 1.0:
                raise ValueError("confidence_fields values must be named confidences within 0..1")
        if self.pitch_hz is not None and self.pitch_hz <= 0:
            raise ValueError("pitch_hz must be positive when known")


@dataclass(frozen=True)
class ContextCorrection:
    """Context-adjusted posterior; never overwrites raw detector evidence."""

    instrument_probabilities: Mapping[str,float] = field(default_factory=dict)
    role_probabilities: Mapping[str,float] = field(default_factory=dict)
    confidence_fields: Mapping[str,float] = field(default_factory=dict)
    reasons: tuple[str,...] = ()

    def validate(self) -> None:
        _validate_probability_map(self.instrument_probabilities,"instrument_probabilities")
        _validate_probability_map(self.role_probabilities,"role_probabilities")
        for key,value in self.confidence_fields.items():
            if not key or not 0.0 <= float(value) <= 1.0:
                raise ValueError("confidence_fields values must be named confidences within 0..1")


@dataclass(frozen=True)
class PerformanceEvidence:
    source_id: str
    timestamp_s: float
    raw: DetectorEvidence
    posterior: ContextCorrection
    musical_position: MusicalScoreCoordinate | None = None
    provenance: tuple[str,...] = ()

    def validate(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.timestamp_s < 0:
            raise ValueError("timestamp_s may not be negative")
        self.raw.validate()
        self.posterior.validate()
        if self.musical_position is not None:
            self.musical_position.validate()


@dataclass(frozen=True)
class MusicalMoment:
    source_id: str
    timestamp_s: float
    density: float | None = None
    tension: float | None = None
    register_center: float | None = None
    tempo_bpm: float | None = None
    beat_position: float | None = None
    harmony_label: str | None = None
    instrument_probabilities: Mapping[str,float] = field(default_factory=dict)
    role_probabilities: Mapping[str,float] = field(default_factory=dict)
    confidence_fields: Mapping[str,float] = field(default_factory=dict)
    musical_position: MusicalScoreCoordinate | None = None
    provenance: tuple[str,...] = ()

    def validate(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.timestamp_s < 0:
            raise ValueError("timestamp_s may not be negative")
        for value,name in ((self.density,"density"),(self.tension,"tension")):
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1 when known")
        if self.tempo_bpm is not None and self.tempo_bpm <= 0:
            raise ValueError("tempo_bpm must be positive when known")
        _validate_probability_map(self.instrument_probabilities,"instrument_probabilities")
        _validate_probability_map(self.role_probabilities,"role_probabilities")
        for key,value in self.confidence_fields.items():
            if not key or not 0.0 <= float(value) <= 1.0:
                raise ValueError("confidence_fields values must be named confidences within 0..1")
        if self.musical_position is not None:
            self.musical_position.validate()


def identity_context_correction(raw: DetectorEvidence) -> ContextCorrection:
    raw.validate()
    return ContextCorrection(
        instrument_probabilities=dict(raw.instrument_probabilities),
        role_probabilities=dict(raw.role_probabilities),
        confidence_fields=dict(raw.confidence_fields),
        reasons=("identity_context_correction:no_context_model",),
    )


def musical_moment_from_evidence(
    evidence: PerformanceEvidence,
    *,
    density: float | None = None,
    tension: float | None = None,
    register_center: float | None = None,
    tempo_bpm: float | None = None,
    beat_position: float | None = None,
    harmony_label: str | None = None,
) -> MusicalMoment:
    evidence.validate()
    moment=MusicalMoment(
        source_id=evidence.source_id,
        timestamp_s=evidence.timestamp_s,
        density=density,
        tension=tension,
        register_center=register_center,
        tempo_bpm=tempo_bpm,
        beat_position=beat_position,
        harmony_label=harmony_label,
        instrument_probabilities=dict(evidence.posterior.instrument_probabilities),
        role_probabilities=dict(evidence.posterior.role_probabilities),
        confidence_fields=dict(evidence.posterior.confidence_fields),
        musical_position=evidence.musical_position,
        provenance=evidence.provenance+("audio_evidence:musical_moment",),
    )
    moment.validate()
    return moment


def structural_event_from_evidence(
    evidence: PerformanceEvidence,
    *,
    event_id: str,
    onset_beats: float | None,
    duration_beats: float | None,
) -> StructuralPerformanceEvent | None:
    """Promote only aligned, beat-domain evidence into structural learning."""
    evidence.validate()
    p=evidence.musical_position
    if p is None or p.bar is None or p.beat is None:
        return None
    if onset_beats is None or duration_beats is None or duration_beats <= 0:
        return None

    raw=evidence.raw
    posterior=evidence.posterior
    pitch_midi=None
    if raw.pitch_hz is not None:
        pitch_midi=69+12*log2(raw.pitch_hz/440.0)
        if not 0 <= pitch_midi <= 127:
            pitch_midi=None
    if pitch_midi is None and not raw.onset:
        return None

    instrument=max(
        posterior.instrument_probabilities,
        key=posterior.instrument_probabilities.get,
        default="",
    )
    role=max(
        posterior.role_probabilities,
        key=posterior.role_probabilities.get,
        default="",
    )
    confidence=float(posterior.confidence_fields.get(
        "event",
        raw.confidence_fields.get("event",raw.confidence_fields.get("pitch",0.5)),
    ))
    event=StructuralPerformanceEvent(
        event_id=event_id,
        onset_beats=onset_beats,
        duration_beats=duration_beats,
        pitch_midi=pitch_midi,
        unpitched_token="" if pitch_midi is not None else "onset",
        instrument=instrument,
        role=role,
        confidence=confidence,
        provenance=evidence.provenance+("audio_evidence:structural_promotion",),
        musical_position=p,
        audio_onset_s=evidence.timestamp_s,
    )
    event.validate()
    return event


__all__=[
    "artifacts_from_audio_aggregate",
    "DetectorEvidence",
    "ContextCorrection",
    "PerformanceEvidence",
    "MusicalMoment",
    "identity_context_correction",
    "musical_moment_from_evidence",
    "structural_event_from_evidence",
]
