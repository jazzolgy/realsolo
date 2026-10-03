"""Instrument-neutral structural data and derived learning artifacts.

Raw audio is analyzed once into StructuralPerformanceData. Every learning domain
consumes that shared structure instead of re-decoding the source independently.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .form_position import FormMap, MetricFormPosition


class LearningDomain(str, Enum):
    MOTIF = "motif"
    SOLO_PHRASE = "solo_phrase"
    VOCABULARY = "vocabulary"
    COMPING = "comping"
    HARMONY_VOICE_LEADING = "harmony_voice_leading"
    RHYTHM_MICROTIMING = "rhythm_microtiming"
    ENSEMBLE_INTERACTION = "ensemble_interaction"
    EXPRESSION = "expression"
    FORM_TENSION = "form_tension"
    STYLE = "style"
    GENRE = "genre"
    RHYTHM_GROOVE = "rhythm_groove"


@dataclass(frozen=True)
class StructuralPerformanceEvent:
    event_id: str
    onset_beats: float
    duration_beats: float
    pitch_midi: float | None = None
    unpitched_token: str = ""
    instrument: str = ""
    role: str = ""
    dynamic: float | None = None
    accent: float = .5
    timing_offset_beats: float = 0.0
    articulation: tuple[str, ...] = ()
    harmony_label: str = ""
    phrase_id: str = ""
    ensemble_role: str = ""
    confidence: float = 1.0
    instrument_probabilities: Mapping[str, float] = field(default_factory=dict)
    role_probabilities: Mapping[str, float] = field(default_factory=dict)
    confidence_fields: Mapping[str, float] = field(default_factory=dict)
    tags: frozenset[str] = frozenset()
    provenance: tuple[str, ...] = ()
    metric_form_position: MetricFormPosition | None = None

    def validate(self) -> None:
        if not self.event_id:
            raise ValueError("event_id is required")
        if self.onset_beats < 0:
            raise ValueError("onset_beats may not be negative")
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")
        if self.pitch_midi is None and not self.unpitched_token:
            raise ValueError("event requires pitch_midi or unpitched_token")
        if self.pitch_midi is not None and not 0.0 <= self.pitch_midi <= 127.0:
            raise ValueError("pitch_midi must be within 0..127")
        if self.dynamic is not None and not 0.0 <= self.dynamic <= 1.0:
            raise ValueError("dynamic must be within 0..1")
        if not 0.0 <= self.accent <= 1.0:
            raise ValueError("accent must be within 0..1")
        if not -1.0 <= self.timing_offset_beats <= 1.0:
            raise ValueError("timing_offset_beats must remain local")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        for mapping, name in ((self.instrument_probabilities, "instrument_probabilities"), (self.role_probabilities, "role_probabilities")):
            total = 0.0
            for key, value in mapping.items():
                if not key or not 0.0 <= float(value) <= 1.0:
                    raise ValueError(f"{name} values must be named probabilities within 0..1")
                total += float(value)
            if mapping and total > 1.000001:
                raise ValueError(f"{name} probabilities may not sum above 1")
        for key, value in self.confidence_fields.items():
            if not key or not 0.0 <= float(value) <= 1.0:
                raise ValueError("confidence_fields values must be named confidences within 0..1")
        if self.metric_form_position is not None:
            self.metric_form_position.validate()


@dataclass(frozen=True)
class StructuralPerformanceData:
    source_id: str
    events: tuple[StructuralPerformanceEvent, ...]
    tempo_bpm: float | None = None
    meter: str = ""
    key_center: str = ""
    form_label: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()
    form_map: FormMap | None = None

    def validate(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.tempo_bpm is not None and self.tempo_bpm <= 0:
            raise ValueError("tempo_bpm must be positive")
        if self.form_map is not None:
            self.form_map.validate()
        for event in self.events:
            event.validate()


@dataclass(frozen=True)
class LearningArtifact:
    artifact_id: str
    source_id: str
    domain: LearningDomain
    feature_schema: str
    features: Mapping[str, object]
    source_event_ids: tuple[str, ...] = ()
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.artifact_id or not self.source_id or not self.feature_schema:
            raise ValueError("artifact_id, source_id and feature_schema are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
