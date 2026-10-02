"""Piano-local interaction state derived from comping research.

These structures are experimental projections for piano policy. They do not claim
to be stable shared-Core ensemble contracts yet.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class PianoDensity:
    """Multidimensional piano density; note count alone is not enough."""

    voice_count: int = 0
    onset_rate: float = 0.0
    sustain_ratio: float = 0.0
    register_span: float = 0.0
    registral_concentration: float = 0.0
    dynamic_weight: float = 0.0
    pedal_blur: float = 0.0

    def validate(self) -> None:
        if self.voice_count < 0:
            raise ValueError("voice_count cannot be negative")
        if self.onset_rate < 0:
            raise ValueError("onset_rate cannot be negative")
        if self.register_span < 0:
            raise ValueError("register_span cannot be negative")
        for name in (
            "sustain_ratio",
            "registral_concentration",
            "dynamic_weight",
            "pedal_blur",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")

    @property
    def intrusion_index(self) -> float:
        """Convenience heuristic while preserving the underlying dimensions."""
        self.validate()
        voice_term = min(self.voice_count / 6.0, 1.0)
        onset_term = min(self.onset_rate / 4.0, 1.0)
        span_term = min(self.register_span / 36.0, 1.0)
        return (
            0.18 * voice_term
            + 0.25 * onset_term
            + 0.12 * self.sustain_ratio
            + 0.10 * span_term
            + 0.10 * self.registral_concentration
            + 0.15 * self.dynamic_weight
            + 0.10 * self.pedal_blur
        )


@dataclass(frozen=True)
class PhraseSpaceWindow:
    """An inferred opportunity for accompaniment, not a reserved future phrase."""

    confidence: float
    start_offset_beats: float = 0.0
    estimated_length_beats: float = 0.0
    source: str = "unknown"

    def validate(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        if self.estimated_length_beats < 0:
            raise ValueError("estimated_length_beats cannot be negative")

    @property
    def usable(self) -> bool:
        self.validate()
        return self.confidence >= 0.65 and self.estimated_length_beats >= 0.5


class EnergyDirection(str, Enum):
    DOWN = "down"
    STABLE = "stable"
    UP = "up"


@dataclass(frozen=True)
class PianoInteractionState:
    """Compact state used to bias immediate comping roles."""

    soloist_activity: float = 0.5
    ensemble_density: float = 0.5
    recent_piano_density: PianoDensity = PianoDensity()
    phrase_space: PhraseSpaceWindow | None = None
    section_energy: float = 0.5
    energy_direction: EnergyDirection = EnergyDirection.STABLE

    def validate(self) -> None:
        for name in ("soloist_activity", "ensemble_density", "section_energy"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        self.recent_piano_density.validate()
        if self.phrase_space is not None:
            self.phrase_space.validate()
