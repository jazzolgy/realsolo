"""Bass-specific performance memory.

Keeps short causal summaries of what the bass has actually committed. This is
instrument memory, not Shared Core form/harmony memory. It is intentionally
small and interpretable so the player can reason about contour, register,
density, articulation, and recent complexity without freezing future notes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from music_intelligence.reasoning.legend_style_core import CandidateEvent


class BassArticulation(str, Enum):
    NEUTRAL = "neutral"
    CONNECTED = "connected"
    SHORT = "short"
    GHOSTED = "ghosted"
    DEAD = "dead"
    ACCENTED = "accented"


@dataclass(frozen=True)
class BassCommittedAction:
    event: CandidateEvent
    accent: float = 0.5
    sounding_length_ratio: float = 0.85
    articulation: BassArticulation = BassArticulation.NEUTRAL
    interaction_role: str = "anchor"
    harmonic_role: str = "unknown"
    metric_role: str = "unknown"

    def validate(self) -> None:
        if not 0.0 <= self.accent <= 1.0:
            raise ValueError("accent must be within 0..1")
        if not 0.0 <= self.sounding_length_ratio <= 1.5:
            raise ValueError("sounding_length_ratio must be within 0..1.5")


@dataclass(frozen=True)
class BassPerformanceSnapshot:
    recent_pitches: tuple[int, ...] = ()
    recent_intervals: tuple[int, ...] = ()
    consecutive_step_count: int = 0
    consecutive_direction_count: int = 0
    phrase_register_center: float | None = None
    phrase_register_slope: float = 0.0
    recent_accent_mean: float = 0.5
    recent_density: float = 0.0
    recent_ghost_count: int = 0
    recent_complexity: float = 0.0
    recent_harmonic_roles: tuple[str, ...] = ()
    recent_metric_roles: tuple[str, ...] = ()

    @property
    def previous_pitch_midi(self) -> int | None:
        return self.recent_pitches[-1] if self.recent_pitches else None

    @property
    def previous_interval_semitones(self) -> int | None:
        return self.recent_intervals[-1] if self.recent_intervals else None


@dataclass
class BassPerformanceMemory:
    committed: list[BassCommittedAction] = field(default_factory=list)
    history_limit: int = 24

    def commit(self, action: BassCommittedAction) -> None:
        action.validate()
        self.committed.append(action)
        if len(self.committed) > self.history_limit:
            self.committed[:] = self.committed[-self.history_limit:]

    def snapshot(self, *, window: int = 8) -> BassPerformanceSnapshot:
        recent = self.committed[-window:]
        pitches = tuple(
            x.event.pitch_midi for x in recent if x.event.pitch_midi is not None
        )
        intervals = tuple(b - a for a, b in zip(pitches, pitches[1:]))

        step_count = 0
        for x in reversed(intervals):
            if 0 < abs(x) <= 2:
                step_count += 1
            else:
                break

        direction_count = 0
        sign: int | None = None
        for x in reversed(intervals):
            if x == 0:
                break
            current = 1 if x > 0 else -1
            if sign is None:
                sign = current
                direction_count = 1
            elif current == sign:
                direction_count += 1
            else:
                break

        center = sum(pitches) / len(pitches) if pitches else None
        slope = 0.0
        if len(pitches) >= 2:
            slope = (pitches[-1] - pitches[0]) / max(1, len(pitches) - 1)

        accent = (
            sum(x.accent for x in recent) / len(recent)
            if recent else .5
        )
        ghost_count = sum(
            x.articulation in {BassArticulation.GHOSTED, BassArticulation.DEAD}
            for x in recent
        )
        structural_recent = [
            x for x in recent
            if "ghost_note" not in x.event.tags
            and x.harmonic_role != "percussive_ghost"
        ]
        harmonic_roles = tuple(x.harmonic_role for x in structural_recent)
        metric_roles = tuple(x.metric_role for x in structural_recent)

        # Complexity is deliberately heuristic: large movement, ghost events,
        # and non-anchor roles all contribute. It is a local player-state signal,
        # not an aesthetic score.
        complexity_parts: list[float] = []
        for x in recent:
            pitch_motion = 0.0
            complexity_parts.append(
                .15
                + (.12 if x.interaction_role not in {"anchor", "hold", "lock"} else 0.0)
                + (.10 if x.articulation in {BassArticulation.GHOSTED, BassArticulation.DEAD} else 0.0)
            )
        if intervals:
            motion = min(1.0, sum(abs(x) for x in intervals) / (len(intervals) * 7.0))
        else:
            motion = 0.0
        recent_complexity = min(
            1.0,
            (sum(complexity_parts) / len(complexity_parts) if complexity_parts else 0.0)
            + .35 * motion,
        )

        return BassPerformanceSnapshot(
            recent_pitches=pitches,
            recent_intervals=intervals,
            consecutive_step_count=step_count,
            consecutive_direction_count=direction_count,
            phrase_register_center=center,
            phrase_register_slope=slope,
            recent_accent_mean=accent,
            recent_density=min(1.0, len(recent) / max(1, window)),
            recent_ghost_count=ghost_count,
            recent_complexity=recent_complexity,
            recent_harmonic_roles=harmonic_roles,
            recent_metric_roles=metric_roles,
        )
