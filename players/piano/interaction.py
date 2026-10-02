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


def blend_density(previous: PianoDensity, current: PianoDensity, alpha: float = 0.6) -> PianoDensity:
    """Exponential smoothing for recent piano activity."""
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be within 0..1")
    previous.validate()
    current.validate()
    beta = 1.0 - alpha
    return PianoDensity(
        voice_count=round(alpha * current.voice_count + beta * previous.voice_count),
        onset_rate=alpha * current.onset_rate + beta * previous.onset_rate,
        sustain_ratio=alpha * current.sustain_ratio + beta * previous.sustain_ratio,
        register_span=alpha * current.register_span + beta * previous.register_span,
        registral_concentration=(
            alpha * current.registral_concentration
            + beta * previous.registral_concentration
        ),
        dynamic_weight=alpha * current.dynamic_weight + beta * previous.dynamic_weight,
        pedal_blur=alpha * current.pedal_blur + beta * previous.pedal_blur,
    )


def decay_density(previous: PianoDensity, factor: float = 0.55) -> PianoDensity:
    """Decay recent piano activity after a silent action."""
    if not 0.0 <= factor <= 1.0:
        raise ValueError("factor must be within 0..1")
    previous.validate()
    return PianoDensity(
        voice_count=round(previous.voice_count * factor),
        onset_rate=previous.onset_rate * factor,
        sustain_ratio=previous.sustain_ratio * factor,
        register_span=previous.register_span * factor,
        registral_concentration=previous.registral_concentration * factor,
        dynamic_weight=previous.dynamic_weight * factor,
        pedal_blur=previous.pedal_blur * factor,
    )


def infer_energy_direction(previous: float | None, current: float, threshold: float = 0.08) -> EnergyDirection:
    """Infer only coarse direction from observed section-energy change."""
    if not 0.0 <= current <= 1.0:
        raise ValueError("current energy must be within 0..1")
    if previous is None:
        return EnergyDirection.STABLE
    if not 0.0 <= previous <= 1.0:
        raise ValueError("previous energy must be within 0..1")
    delta = current - previous
    if delta >= threshold:
        return EnergyDirection.UP
    if delta <= -threshold:
        return EnergyDirection.DOWN
    return EnergyDirection.STABLE
