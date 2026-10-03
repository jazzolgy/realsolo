from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from music_intelligence.learning.form_position import MetricFormPosition


class ObservationKind(str, Enum):
    NOTE_ON = "note_on"
    NOTE_OFF = "note_off"
    CONTROL_CHANGE = "control_change"
    AUDIO_FRAME = "audio_frame"
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
class AudioObservation:
    """Low-latency audio evidence, not a transcription result."""

    timestamp: float
    rms: float
    peak: float
    onset_strength: float = 0.0
    onset: bool = False
    pitch_hz: float | None = None
    pitch_confidence: float = 0.0
    spectral_centroid_hz: float | None = None
    spectral_flatness: float | None = None
    zero_crossing_rate: float | None = None
    low_energy_ratio: float | None = None
    mid_energy_ratio: float | None = None
    high_energy_ratio: float | None = None
    kind: ObservationKind = ObservationKind.AUDIO_FRAME

    @property
    def is_attack(self) -> bool:
        return self.onset

    @property
    def velocity(self) -> int:
        # A bounded perceptual proxy; Core should use continuous audio evidence too.
        return int(max(0, min(127, round(self.rms * 420.0))))

    @property
    def note(self) -> int | None:
        if self.pitch_hz is None or self.pitch_hz <= 0 or self.pitch_confidence < 0.45:
            return None
        import math
        return int(round(69 + 12 * math.log2(self.pitch_hz / 440.0)))


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
    input_mode: str = "unknown"
    audio_rms: float = 0.0
    audio_peak: float = 0.0
    audio_onset_strength: float = 0.0
    audio_pitch_hz: float | None = None
    audio_pitch_confidence: float = 0.0
    metric_form_position: MetricFormPosition | None = None


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
