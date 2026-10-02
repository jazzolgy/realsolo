"""v1.39 harmonic rhythm + local key / tonicization intelligence.

This layer adds time to harmony. A chord/function hypothesis is not interpreted
in isolation: duration, metric stress, repetition, cadence proximity, and local
target persistence all affect whether the system hears a passing tonicization,
a key-of-the-moment region, or a stronger modulation-like state.

It is instrument-neutral and stores no future note sequence.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class KeyRegionStrength(str, Enum):
    GLOBAL = "global"
    SECTIONAL = "sectional"
    LOCAL = "local"
    TONICIZATION = "tonicization"
    TRANSIENT = "transient"
    UNKNOWN = "unknown"


class CadenceStrength(str, Enum):
    NONE = "none"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


@dataclass(frozen=True)
class HarmonicSpan:
    span_id: str
    start_beat: float
    duration_beats: float
    root_pc: int | None = None
    symbol: str | None = None
    function: str | None = None
    local_tonic_pc: int | None = None
    metric_strength: float = .5
    arrival_strength: float = .0
    continuation_strength: float = .0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")
        for pc in (self.root_pc, self.local_tonic_pc):
            if pc is not None and not 0 <= pc <= 11:
                raise ValueError("pitch class must be in 0..11")
        for value, name in (
            (self.metric_strength, "metric_strength"),
            (self.arrival_strength, "arrival_strength"),
            (self.continuation_strength, "continuation_strength"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


@dataclass(frozen=True)
class HarmonicRhythmSummary:
    mean_span_beats: float
    median_span_beats: float
    changes_per_4_beats: float
    acceleration: float
    deceleration: float
    stability: float


@dataclass(frozen=True)
class LocalKeyHypothesis:
    tonic_pc: int
    label: str | None = None
    support: float = 0.0
    cadence_support: float = 0.0
    dominant_support: float = 0.0
    duration_support: float = 0.0
    repetition_support: float = 0.0
    section_support: float = 0.0
    strength: KeyRegionStrength = KeyRegionStrength.UNKNOWN
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not 0 <= self.tonic_pc <= 11:
            raise ValueError("tonic_pc must be in 0..11")
        for value in (
            self.support,
            self.cadence_support,
            self.dominant_support,
            self.duration_support,
            self.repetition_support,
            self.section_support,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError("support values must be within 0..1")


@dataclass(frozen=True)
class TonicizationEvidence:
    tonic_pc: int
    dominant_root_pc: int | None = None
    has_predominant: bool = False
    resolves_to_target: bool = False
    target_duration_beats: float = 0.0
    target_repetitions: int = 0
    cadence_strength: CadenceStrength = CadenceStrength.NONE
    section_boundary_alignment: float = 0.0
    return_to_parent_key: float = 0.0

    def validate(self) -> None:
        if not 0 <= self.tonic_pc <= 11:
            raise ValueError("tonic_pc must be in 0..11")
        if self.dominant_root_pc is not None and not 0 <= self.dominant_root_pc <= 11:
            raise ValueError("dominant_root_pc must be in 0..11")
        if self.target_duration_beats < 0:
            raise ValueError("target_duration_beats may not be negative")
        if self.target_repetitions < 0:
            raise ValueError("target_repetitions may not be negative")
        for value in (self.section_boundary_alignment, self.return_to_parent_key):
            if not 0.0 <= value <= 1.0:
                raise ValueError("evidence values must be within 0..1")


def _median(values: Sequence[float]) -> float:
    s = sorted(values)
    n = len(s)
    if not n:
        return 0.0
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def summarize_harmonic_rhythm(spans: Sequence[HarmonicSpan]) -> HarmonicRhythmSummary:
    if not spans:
        return HarmonicRhythmSummary(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    for s in spans:
        s.validate()

    durations = [s.duration_beats for s in spans]
    total = sum(durations)
    mean = total / len(durations)
    changes_per_4 = (len(spans) / total) * 4.0 if total else 0.0

    acceleration = deceleration = 0.0
    comparisons = 0
    for a, b in zip(durations, durations[1:]):
        comparisons += 1
        if b < a:
            acceleration += min(1.0, (a - b) / max(a, 1e-9))
        elif b > a:
            deceleration += min(1.0, (b - a) / max(b, 1e-9))
    if comparisons:
        acceleration /= comparisons
        deceleration /= comparisons

    # Stability here means relative regularity of harmonic span duration, not
    # tonal stability.
    spread = (max(durations) - min(durations)) / max(max(durations), 1e-9)
    stability = max(0.0, 1.0 - spread)

    return HarmonicRhythmSummary(
        mean,
        _median(durations),
        changes_per_4,
        acceleration,
        deceleration,
        stability,
    )


def infer_local_key(e: TonicizationEvidence) -> LocalKeyHypothesis:
    e.validate()

    dominant_support = .0
    if e.dominant_root_pc is not None:
        expected = (e.dominant_root_pc - 5) % 12
        if expected == e.tonic_pc:
            dominant_support = .75
        else:
            sub_expected = (e.dominant_root_pc - 1) % 12
            if sub_expected == e.tonic_pc:
                dominant_support = .62

    if e.has_predominant:
        dominant_support = min(1.0, dominant_support + .12)
    if e.resolves_to_target:
        dominant_support = min(1.0, dominant_support + .13)

    cadence_map = {
        CadenceStrength.NONE: 0.0,
        CadenceStrength.WEAK: .25,
        CadenceStrength.MODERATE: .58,
        CadenceStrength.STRONG: .90,
    }
    cadence_support = cadence_map[e.cadence_strength]

    duration_support = min(1.0, e.target_duration_beats / 16.0)
    repetition_support = min(1.0, e.target_repetitions / 4.0)
    section_support = e.section_boundary_alignment

    support = (
        .28 * dominant_support
        + .24 * cadence_support
        + .18 * duration_support
        + .12 * repetition_support
        + .18 * section_support
    )

    # Strong evidence of return to parent key keeps a local tonic from being
    # promoted too aggressively.
    support *= 1.0 - .30 * e.return_to_parent_key

    if support >= .78 and section_support >= .65:
        strength = KeyRegionStrength.SECTIONAL
    elif support >= .62 and duration_support >= .45:
        strength = KeyRegionStrength.LOCAL
    elif support >= .38:
        strength = KeyRegionStrength.TONICIZATION
    else:
        strength = KeyRegionStrength.TRANSIENT

    return LocalKeyHypothesis(
        tonic_pc=e.tonic_pc,
        support=support,
        cadence_support=cadence_support,
        dominant_support=dominant_support,
        duration_support=duration_support,
        repetition_support=repetition_support,
        section_support=section_support,
        strength=strength,
        provenance=("harmonic_time_v139",),
    )


def key_of_the_moment_score(h: LocalKeyHypothesis) -> float:
    h.validate()
    if h.strength in {KeyRegionStrength.LOCAL, KeyRegionStrength.SECTIONAL}:
        return min(1.0, h.support + .08)
    if h.strength is KeyRegionStrength.TONICIZATION:
        return h.support
    return max(0.0, h.support - .10)
