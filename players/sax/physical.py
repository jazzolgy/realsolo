"""Generic Sax physical-feasibility layer.

Parker-specific physical tendencies do not belong here.  This model describes
instrument/player feasibility supplied by the caller.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SaxPhysicalConstraints:
    lowest_playable_midi: int
    highest_playable_midi: int
    comfortable_interval_semitones: int
    max_notes_since_breath: int
    max_beats_since_breath: float

    def validate(self) -> None:
        if self.lowest_playable_midi >= self.highest_playable_midi:
            raise ValueError("invalid sax range")
        if self.comfortable_interval_semitones < 0:
            raise ValueError("comfortable interval cannot be negative")
        if self.max_notes_since_breath <= 0 or self.max_beats_since_breath <= 0:
            raise ValueError("breath capacity must be positive")


@dataclass(frozen=True)
class SaxPhysicalAssessment:
    feasible: bool
    transition_cost: float
    breath_pressure: float
    reasons: tuple[str, ...] = ()


def assess_sax_transition(
    *,
    pitch_midi: int,
    previous_pitch_midi: int | None,
    notes_since_breath: int,
    beats_since_breath: float,
    constraints: SaxPhysicalConstraints,
) -> SaxPhysicalAssessment:
    constraints.validate()
    reasons: list[str] = []

    if not constraints.lowest_playable_midi <= pitch_midi <= constraints.highest_playable_midi:
        return SaxPhysicalAssessment(False, 1.0, 1.0, ("outside configured playable range",))

    interval = abs(pitch_midi - previous_pitch_midi) if previous_pitch_midi is not None else 0
    extra = max(0, interval - constraints.comfortable_interval_semitones)
    transition_cost = min(1.0, extra / max(1, constraints.comfortable_interval_semitones))

    note_pressure = notes_since_breath / constraints.max_notes_since_breath
    beat_pressure = beats_since_breath / constraints.max_beats_since_breath
    breath_pressure = min(1.0, max(note_pressure, beat_pressure))

    if transition_cost > 0:
        reasons.append("large transition relative to configured comfort")
    if breath_pressure >= 0.8:
        reasons.append("breath capacity nearing configured limit")

    return SaxPhysicalAssessment(True, transition_cost, breath_pressure, tuple(reasons))
