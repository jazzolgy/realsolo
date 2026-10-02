"""Instrument-neutral motif representation.

A motif stores identity, not an exact future phrase. Interval/rhythm schemas are
relative abstractions that Players may realize differently.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class MotifSourceType(str, Enum):
    GENERATIVE_NEW = "generative_new"
    VOCABULARY_SEEDED = "vocabulary_seeded"
    ENSEMBLE_DERIVED = "ensemble_derived"
    SELF_MEMORY_DERIVED = "self_memory_derived"
    LEGEND_PRIOR_DERIVED = "legend_prior_derived"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class MotifIdentity:
    motif_id: str
    interval_schema: tuple[int, ...] = ()
    rhythm_schema: tuple[float, ...] = ()
    contour: str = ""
    accent_shape: tuple[float, ...] = ()
    phrase_shape: str = ""
    density: float = .5
    harmonic_target_behavior: str = ""
    tension_shape: str = ""
    interaction_function: str = ""
    event_count_hint: int = 3
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.motif_id:
            raise ValueError("motif_id is required")
        if not 1 <= self.event_count_hint <= 8:
            raise ValueError("event_count_hint must be within 1..8")
        if not 0.0 <= self.density <= 1.0:
            raise ValueError("density must be within 0..1")
        if self.rhythm_schema and any(x <= 0 for x in self.rhythm_schema):
            raise ValueError("rhythm_schema values must be positive")
        if self.accent_shape and any(not 0.0 <= x <= 1.0 for x in self.accent_shape):
            raise ValueError("accent_shape must be within 0..1")


@dataclass(frozen=True)
class MotifCandidate:
    identity: MotifIdentity
    source_type: MotifSourceType
    generation_weight: float = .5
    learned_weight: float = 0.0
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        self.identity.validate()
        if not 0.0 <= self.generation_weight <= 1.0:
            raise ValueError("generation_weight must be within 0..1")
        if not -1.0 <= self.learned_weight <= 1.0:
            raise ValueError("learned_weight must be within -1..1")
