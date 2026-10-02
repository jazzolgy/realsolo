"""Automatic pattern-consistency context from harmonic/form history.

This module does not interpret jazz harmony theory. It observes identities already
present in Shared Core HarmonicFrame and estimates whether the current local context
supports maintaining a comping pattern.

Important distinction:
- frequent chord changes do not necessarily imply low consistency;
- a recurring harmonic cycle (e.g. a vamp) can support strong pattern identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from music_intelligence.harmony.jazz_harmony_core import HarmonicEvidence, HarmonicFrame


@dataclass(frozen=True)
class HarmonicFingerprint:
    root_pc: int | None
    symbol: str | None
    function: str | None
    local_key: str | None

    @classmethod
    def from_frame(cls, frame: HarmonicFrame) -> "HarmonicFingerprint":
        frame.validate()
        evidence = frame.inferred or frame.observed or frame.expected
        if evidence is None:
            return cls(None, None, None, None)
        return cls(
            root_pc=evidence.root_pc,
            symbol=evidence.symbol,
            function=evidence.function,
            local_key=evidence.local_key,
        )


@dataclass(frozen=True)
class HarmonicContinuityFeatures:
    hold_stability: float
    change_rate: float
    recurrence_strength: float
    boundary_pressure: float
    pattern_consistency_strength: float

    def validate(self) -> None:
        for name in (
            "hold_stability",
            "change_rate",
            "recurrence_strength",
            "boundary_pressure",
            "pattern_consistency_strength",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _change_rate(items: Sequence[HarmonicFingerprint]) -> float:
    if len(items) < 2:
        return 0.0
    transitions = sum(1 for a, b in zip(items, items[1:]) if a != b)
    return transitions / (len(items) - 1)


def _hold_stability(items: Sequence[HarmonicFingerprint]) -> float:
    if not items:
        return 0.0
    last = items[-1]
    run = 1
    for item in reversed(items[:-1]):
        if item != last:
            break
        run += 1
    return _clamp((run - 1) / 3.0)


def _recurrence_strength(items: Sequence[HarmonicFingerprint]) -> float:
    """Detect short repeated harmonic cycles without naming their theory."""
    n = len(items)
    best = 0.0
    for cycle_len in (1, 2, 3, 4):
        if n < cycle_len * 2:
            continue
        a = items[-cycle_len:]
        b = items[-2 * cycle_len:-cycle_len]
        matches = sum(1 for x, y in zip(a, b) if x == y)
        ratio = matches / cycle_len
        # Longer coherent cycles are slightly stronger evidence than a single repeat.
        length_weight = {1: 0.72, 2: 0.88, 3: 0.94, 4: 1.0}[cycle_len]
        best = max(best, ratio * length_weight)
    return _clamp(best)


def _boundary_pressure(frame: HarmonicFrame) -> float:
    """Estimate local form/phrase-boundary pressure from existing Core fields."""
    phrase = frame.phrase_position
    phrase_pressure = _clamp((phrase - 0.72) / 0.28)

    cadence = (frame.cadence_state or "open").strip().lower()
    cadence_pressure = 0.0 if cadence in {"", "open", "none"} else 0.35

    next_change = 0.0
    current = HarmonicFingerprint.from_frame(frame)
    if frame.next_expected is not None:
        next_fp = HarmonicFingerprint(
            frame.next_expected.root_pc,
            frame.next_expected.symbol,
            frame.next_expected.function,
            frame.next_expected.local_key,
        )
        if next_fp != current:
            next_change = 0.15

    return _clamp(max(phrase_pressure, cadence_pressure) + next_change)


def estimate_harmonic_continuity(
    frame: HarmonicFrame,
    history: Sequence[HarmonicFingerprint],
) -> HarmonicContinuityFeatures:
    """Estimate a soft pattern-consistency prior for the current tick.

    High recurrence can offset a high raw chord-change rate, preserving vamp/cycle
    identity. Form-boundary pressure lowers consistency so texture can reset.
    """
    frame.validate()
    current = HarmonicFingerprint.from_frame(frame)
    items = tuple(history[-7:]) + (current,)

    hold = _hold_stability(items)
    change = _change_rate(items)
    recurrence = _recurrence_strength(items)
    boundary = _boundary_pressure(frame)

    continuity_base = max(hold, recurrence)
    change_penalty = 0.38 * change * (1.0 - recurrence)
    consistency = _clamp(
        0.12
        + 0.58 * continuity_base
        + 0.16 * recurrence
        - change_penalty
        - 0.42 * boundary
    )

    result = HarmonicContinuityFeatures(
        hold_stability=hold,
        change_rate=change,
        recurrence_strength=recurrence,
        boundary_pressure=boundary,
        pattern_consistency_strength=consistency,
    )
    result.validate()
    return result


@dataclass
class HarmonicContinuityMemory:
    history: list[HarmonicFingerprint]

    def __init__(self) -> None:
        self.history = []

    def observe(self, frame: HarmonicFrame) -> HarmonicContinuityFeatures:
        features = estimate_harmonic_continuity(frame, self.history)
        self.history.append(HarmonicFingerprint.from_frame(frame))
        if len(self.history) > 8:
            del self.history[:-8]
        return features
