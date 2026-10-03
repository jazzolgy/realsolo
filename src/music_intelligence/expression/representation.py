"""Shared expressive realization representation.

This layer answers HOW an already chosen musical event/gesture should be
expressed. It does not choose pitches, voicings, lick identity, or future note
sequences.

Shared Core expresses perceptual musical intent. Players map that intent to
instrument-specific controls such as piano velocity/pedal/touch, sax breath and
vibrato, bass pluck/release, or drum stroke/cymbal choice.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.learning.score_alignment import MusicalScoreCoordinate


class ExpressionContour(str, Enum):
    STABLE = "stable"
    RISE = "rise"
    FALL = "fall"
    RISE_FALL = "rise_fall"
    FALL_RISE = "fall_rise"
    CONTRAST = "contrast"


class ExpressivePhase(str, Enum):
    ENTRY = "entry"
    DEVELOP = "develop"
    PEAK = "peak"
    RELEASE = "release"
    AFTERGLOW = "afterglow"


@dataclass(frozen=True)
class RelativeExpressionProfile:
    """Reusable phrase/vocabulary HOW-profile, independent of absolute loudness.

    Values are relative musical tendencies. They may come from a vocabulary
    item, motif memory, phrase memory, or learned expressive evidence.
    """

    profile_id: str
    contour: ExpressionContour = ExpressionContour.STABLE
    entry_relative: float = 0.0
    peak_relative: float = 0.0
    release_relative: float = 0.0
    accent_bias: float = 0.0
    body_bias: float = 0.0
    foreground_bias: float = 0.0
    timing_bias_beats: float = 0.0
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.profile_id:
            raise ValueError("profile_id is required")
        for name in (
            "entry_relative","peak_relative","release_relative",
            "accent_bias","body_bias","foreground_bias",
        ):
            if not -1.0 <= getattr(self,name) <= 1.0:
                raise ValueError(f"{name} must be within -1..1")
        if not -0.5 <= self.timing_bias_beats <= 0.5:
            raise ValueError("timing_bias_beats must remain local")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class ExpressiveContext:
    """Context for one immediate expressive decision."""

    position: MusicalScoreCoordinate | None = None
    phrase_maturity: float = 0.0
    tension: float = 0.0
    ensemble_density: float = 0.5
    current_foreground_weight: float = 0.5
    target_foreground_weight: float = 0.5
    register_height: float = 0.5
    repetition_index: int = 0
    boundary_pressure: float = 0.0
    climax_pressure: float = 0.0
    release_pressure: float = 0.0
    expressive_phase: ExpressivePhase = ExpressivePhase.DEVELOP

    def validate(self) -> None:
        for name in (
            "phrase_maturity","tension","ensemble_density",
            "current_foreground_weight","target_foreground_weight",
            "register_height","boundary_pressure","climax_pressure",
            "release_pressure",
        ):
            if not 0.0 <= getattr(self,name) <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.repetition_index < 0:
            raise ValueError("repetition_index may not be negative")
        if self.position is not None:
            self.position.validate()


@dataclass(frozen=True)
class ExpressiveIntent:
    """Instrument-neutral HOW intention for the current event/gesture."""

    perceptual_intensity: float = 0.5
    dynamic_level: float = 0.5
    accent_strength: float = 0.5
    note_body: float = 0.5
    timing_emphasis_beats: float = 0.0
    foreground_weight: float = 0.5
    contour: ExpressionContour = ExpressionContour.STABLE
    articulation_tags: frozenset[str] = frozenset()
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        for name in (
            "perceptual_intensity","dynamic_level","accent_strength",
            "note_body","foreground_weight","confidence",
        ):
            if not 0.0 <= getattr(self,name) <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if not -0.5 <= self.timing_emphasis_beats <= 0.5:
            raise ValueError("timing_emphasis_beats must remain local")
