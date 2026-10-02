"""Drummer-specific runtime semantics.

This module is an instrument-owned realization layer.  It consumes projections
from Shared Core / Shared Harmony but does not redefine form, phrase, ensemble,
narrative, memory, or harmony theory.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.harmony import HarmonicFrame


class DrumVoice(str, Enum):
    RIDE = "ride"
    CLOSED_HIHAT = "closed_hihat"
    OPEN_HIHAT = "open_hihat"
    SNARE = "snare"
    BASS_DRUM = "bass_drum"
    CRASH = "crash"
    HIGH_TOM = "high_tom"
    MID_TOM = "mid_tom"
    FLOOR_TOM = "floor_tom"


class Limb(str, Enum):
    LEFT_HAND = "left_hand"
    RIGHT_HAND = "right_hand"
    LEFT_FOOT = "left_foot"
    RIGHT_FOOT = "right_foot"


class GestureRole(str, Enum):
    TIME = "time"
    COMP = "comp"
    SETUP = "setup"
    FILL = "fill"
    ACCENT = "accent"
    SPACE = "space"


class TimeFeel(str, Enum):
    SWING = "swing"
    STRAIGHT = "straight"


@dataclass(frozen=True)
class DrumHit:
    voice: DrumVoice
    limb: Limb
    velocity: int
    microtiming_ms: float = 0.0
    articulation: str = "normal"

    def validate(self) -> None:
        if not 1 <= self.velocity <= 127:
            raise ValueError("velocity must be within MIDI range 1..127")
        if abs(self.microtiming_ms) > 80:
            raise ValueError("microtiming_ms is a local expressive offset, not future scheduling")


@dataclass(frozen=True)
class DrumGesture:
    """One immediate drum-set decision.

    A gesture may contain simultaneous/near-simultaneous kit hits.  It is not a
    precomposed future pattern.
    """
    hits: tuple[DrumHit, ...] = ()
    role: GestureRole = GestureRole.SPACE
    tags: frozenset[str] = frozenset()
    confidence: float = 1.0
    provenance: tuple[str, ...] = ("drum_player",)

    def validate(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        if not self.hits and self.role is not GestureRole.SPACE:
            raise ValueError("an empty gesture must explicitly mean SPACE")

        used_limbs: set[Limb] = set()
        for hit in self.hits:
            hit.validate()
            if hit.limb in used_limbs:
                raise ValueError("one limb cannot strike two voices in the same immediate gesture")
            used_limbs.add(hit.limb)


@dataclass(frozen=True)
class DrummerSoftPlan:
    """Slow-brain intention without a frozen future drum sequence."""
    feel: TimeFeel = TimeFeel.SWING
    energy: float = 0.5
    comping_density: float = 0.35
    interaction_intent: str = "support"
    ride_velocity: int = 76
    microtiming_bias_ms: float = 0.0
    expressive_timing_offset_ms: float = 0.0
    exact_future_gestures: tuple[DrumGesture, ...] = ()

    def validate(self) -> None:
        if not 0.0 <= self.energy <= 1.0:
            raise ValueError("energy must be within 0..1")
        if not 0.0 <= self.comping_density <= 1.0:
            raise ValueError("comping_density must be within 0..1")
        if not 1 <= self.ride_velocity <= 127:
            raise ValueError("ride_velocity must be within MIDI range 1..127")
        if abs(self.microtiming_bias_ms) > 50:
            raise ValueError("plan microtiming bias is implausibly large")
        if abs(self.expressive_timing_offset_ms) > 50:
            raise ValueError("expressive timing intention is implausibly large")
        if self.exact_future_gestures:
            raise ValueError("DrummerSoftPlan may not freeze future drum gestures")


@dataclass(frozen=True)
class DrummerRuntimeContext:
    """Read-only drummer view of shared musical state plus current clock position.

    phrase_position, ensemble_activity, energy_target and structural flags are
    projections supplied by Shared Core.  HarmonicFrame remains owned by Shared
    Harmony and is consumed read-only.
    """
    position_in_bar_beats: float
    tempo_bpm: float = 140.0
    beats_per_bar: int = 4
    phrase_position: float = 0.0
    ensemble_activity: float = 0.5
    soloist_activity: float = 0.5
    energy_target: float = 0.5
    section_transition: bool = False
    requested_kick: bool = False
    harmonic_transition_confidence: float = 0.0
    harmony: HarmonicFrame | None = None

    def validate(self) -> None:
        if self.tempo_bpm <= 0:
            raise ValueError("tempo_bpm must be positive")
        if self.beats_per_bar <= 0:
            raise ValueError("beats_per_bar must be positive")
        if not 0.0 <= self.position_in_bar_beats < self.beats_per_bar:
            raise ValueError("position_in_bar_beats must be inside the current bar")
        for name in (
            "phrase_position",
            "ensemble_activity",
            "soloist_activity",
            "energy_target",
            "harmonic_transition_confidence",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.harmony is not None:
            self.harmony.validate()
