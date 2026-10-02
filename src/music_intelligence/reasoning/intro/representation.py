"""Shared representation contracts for intro understanding and entry."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class IntroMode(str, Enum):
    VOCAL_COUNT_IN = "vocal_count_in"
    INSTRUMENT_PICKUP = "instrument_pickup"
    RUBATO_SOLO = "rubato_solo"
    PEDAL_POINT = "pedal_point"
    OSTINATO = "ostinato"
    GROOVE_VAMP = "groove_vamp"
    WRITTEN_INTRO = "written_intro"
    FREE_COLLECTIVE = "free_collective"
    DIRECT_HEAD = "direct_head"
    UNKNOWN = "unknown"


class IntroPhase(str, Enum):
    PRE_START = "pre_start"
    INTRO_LISTENING = "intro_listening"
    ENTRY_NEGOTIATION = "entry_negotiation"
    ENTRY_PENDING = "entry_pending"
    ENTRY_COMMITTED = "entry_committed"
    NORMAL_ENSEMBLE_RUNTIME = "normal_ensemble_runtime"


class EntryAction(str, Enum):
    WAIT = "wait"
    SHADOW = "shadow"
    LIGHT_SUPPORT = "light_support"
    PARTIAL_JOIN = "partial_join"
    FULL_JOIN = "full_join"


@dataclass(frozen=True)
class IntroModeHypothesis:
    mode: IntroMode
    confidence: float

    def validate(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("mode confidence must be within 0..1")


@dataclass(frozen=True)
class MeterHypothesis:
    numerator: int
    denominator: int = 4
    confidence: float = 0.0

    def validate(self) -> None:
        if self.numerator <= 0 or self.denominator <= 0:
            raise ValueError("meter values must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("meter confidence must be within 0..1")


@dataclass(frozen=True)
class IntroObservation:
    """One newly perceived slice of evidence.

    This intentionally contains evidence and soft semantic cues, not a future
    phrase. Each runtime tick consumes one observation, commits at most one
    shared entry action, and then listens again.
    """

    timestamp: float
    source_player_id: str | None = None

    # Timing evidence.
    detected_onset: bool = False
    iois_seconds: tuple[float, ...] = ()
    beat_phase_hint: float | None = None
    meter_hint: tuple[int, int] | None = None

    # Semantic cue evidence from upstream perception / UMR.
    vocal_count_confidence: float = 0.0
    pickup_confidence: float = 0.0
    rubato_confidence: float = 0.0
    pedal_confidence: float = 0.0
    ostinato_confidence: float = 0.0
    vamp_confidence: float = 0.0
    written_intro_confidence: float = 0.0
    free_collective_confidence: float = 0.0
    direct_head_confidence: float = 0.0

    # Entry-oriented musical evidence.
    harmonic_arrival_confidence: float = 0.0
    expected_head_harmony_match: float = 0.0
    explicit_entry_cue_confidence: float = 0.0
    phrase_boundary_confidence: float = 0.0
    leader_hold_confidence: float = 0.0

    # Broad musical state.
    ensemble_energy: float = 0.0
    dynamic_intent: float = 0.5
    observed_harmony_id: str | None = None
    expected_head_harmony_id: str | None = None
    tags: frozenset[str] = frozenset()

    def validate(self) -> None:
        if self.timestamp < 0:
            raise ValueError("timestamp may not be negative")
        for value, name in (
            (self.vocal_count_confidence, "vocal_count_confidence"),
            (self.pickup_confidence, "pickup_confidence"),
            (self.rubato_confidence, "rubato_confidence"),
            (self.pedal_confidence, "pedal_confidence"),
            (self.ostinato_confidence, "ostinato_confidence"),
            (self.vamp_confidence, "vamp_confidence"),
            (self.written_intro_confidence, "written_intro_confidence"),
            (self.free_collective_confidence, "free_collective_confidence"),
            (self.direct_head_confidence, "direct_head_confidence"),
            (self.harmonic_arrival_confidence, "harmonic_arrival_confidence"),
            (self.expected_head_harmony_match, "expected_head_harmony_match"),
            (self.explicit_entry_cue_confidence, "explicit_entry_cue_confidence"),
            (self.phrase_boundary_confidence, "phrase_boundary_confidence"),
            (self.leader_hold_confidence, "leader_hold_confidence"),
            (self.ensemble_energy, "ensemble_energy"),
            (self.dynamic_intent, "dynamic_intent"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.beat_phase_hint is not None and not 0.0 <= self.beat_phase_hint < 1.0:
            raise ValueError("beat_phase_hint must be within [0,1)")
        if any(x <= 0 for x in self.iois_seconds):
            raise ValueError("IOIs must be positive")
        if self.meter_hint is not None and (
            self.meter_hint[0] <= 0 or self.meter_hint[1] <= 0
        ):
            raise ValueError("meter_hint values must be positive")


@dataclass(frozen=True)
class IntroState:
    phase: IntroPhase = IntroPhase.PRE_START
    mode_hypotheses: tuple[IntroModeHypothesis, ...] = (
        IntroModeHypothesis(IntroMode.UNKNOWN, 1.0),
    )
    leader_player_id: str | None = None

    pulse_confidence: float = 0.0
    tempo_estimate_bpm: float | None = None
    tempo_stability: float = 0.0
    meter_hypotheses: tuple[MeterHypothesis, ...] = ()
    beat_phase_confidence: float = 0.0

    rubato_probability: float = 0.0
    observed_harmony_id: str | None = None
    expected_head_harmony_id: str | None = None
    pickup_probability: float = 0.0

    entry_readiness: float = 0.0
    entry_permission: float = 0.0
    entry_target_beat_phase: float | None = None
    join_confidence: float = 0.0

    ensemble_energy: float = 0.0
    dynamic_intent: float = 0.5
    ambiguity: float = 1.0
    generation: int = 0
    last_timestamp: float | None = None
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        for h in self.mode_hypotheses:
            h.validate()
        for h in self.meter_hypotheses:
            h.validate()
        for value, name in (
            (self.pulse_confidence, "pulse_confidence"),
            (self.tempo_stability, "tempo_stability"),
            (self.beat_phase_confidence, "beat_phase_confidence"),
            (self.rubato_probability, "rubato_probability"),
            (self.pickup_probability, "pickup_probability"),
            (self.entry_readiness, "entry_readiness"),
            (self.entry_permission, "entry_permission"),
            (self.join_confidence, "join_confidence"),
            (self.ensemble_energy, "ensemble_energy"),
            (self.dynamic_intent, "dynamic_intent"),
            (self.ambiguity, "ambiguity"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.tempo_estimate_bpm is not None and self.tempo_estimate_bpm <= 0:
            raise ValueError("tempo_estimate_bpm must be positive")
        if (
            self.entry_target_beat_phase is not None
            and not 0.0 <= self.entry_target_beat_phase < 1.0
        ):
            raise ValueError("entry_target_beat_phase must be within [0,1)")
        if self.generation < 0:
            raise ValueError("generation may not be negative")
        if self.last_timestamp is not None and self.last_timestamp < 0:
            raise ValueError("last_timestamp may not be negative")


@dataclass(frozen=True)
class EntryDecision:
    action: EntryAction
    readiness: float
    permission: float
    confidence: float
    target_beat_phase: float | None = None
    rationale: tuple[str, ...] = ()

    def validate(self) -> None:
        for value, name in (
            (self.readiness, "readiness"),
            (self.permission, "permission"),
            (self.confidence, "confidence"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.target_beat_phase is not None and not 0.0 <= self.target_beat_phase < 1.0:
            raise ValueError("target_beat_phase must be within [0,1)")


def with_generation(state: IntroState, **changes: object) -> IntroState:
    return replace(state, generation=state.generation + 1, **changes)
