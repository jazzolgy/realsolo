from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ObservationKind(str, Enum):
    NOTE_ON = "note_on"
    NOTE_OFF = "note_off"
    CONTROL_CHANGE = "control_change"
    CLOCK_TICK = "clock_tick"


@dataclass(frozen=True, slots=True)
class MidiObservation:
    timestamp: float
    kind: ObservationKind
    note: int | None = None
    velocity: int = 0
    channel: int = 0
    control: int | None = None
    value: int | None = None

    @property
    def is_attack(self) -> bool:
        return self.kind == ObservationKind.NOTE_ON and self.note is not None and self.velocity > 0


@dataclass(frozen=True, slots=True)
class BeatState:
    tempo_bpm: float | None = None
    beat_period_s: float | None = None
    phase: float | None = None
    confidence: float = 0.0
    anchor_time: float | None = None


@dataclass(frozen=True, slots=True)
class PhraseState:
    active: bool = False
    attack_count: int = 0
    last_attack_time: float | None = None
    last_pitch: int | None = None
    mean_velocity: float = 0.0
    phrase_end: bool = False
    silence_beats: float = 0.0


@dataclass(frozen=True, slots=True)
class EnsembleState:
    now: float = 0.0
    beat: BeatState = field(default_factory=BeatState)
    phrase: PhraseState = field(default_factory=PhraseState)
    active_notes: frozenset[int] = frozenset()
    human_activity: float = 0.0
    leader: str = "human"
    ai_role: str = "following"
    revision: int = 0


@dataclass(frozen=True, slots=True)
class MusicalAction:
    """One committed musical event; transport may expand it to note-on/note-off."""

    pitch_midi: int
    velocity: int
    duration_s: float
    delay_s: float = 0.0
    channel: int = 0
    reason: str = ""


@dataclass(frozen=True, slots=True)
class TransportEvent:
    kind: str
    pitch_midi: int
    velocity: int
    channel: int
