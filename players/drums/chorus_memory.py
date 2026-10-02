"""Local drummer chorus-scale execution memory.

Shared Core owns canonical form/narrative. This module stores only the drummer's
own recent activity history across the current form so it can decide when to
back off, preserve headroom, or prepare a re-entry.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import DrumGesture, GestureRole


@dataclass(frozen=True)
class BebopChorusMemory:
    recent_8bar_density: float = 0.0
    bars_since_major_statement: float = 999.0
    climax_already_supported: bool = False
    need_to_back_off: bool = False
    next_form_boundary_distance_bars: float | None = None

    def validate(self) -> None:
        if not 0.0 <= self.recent_8bar_density <= 1.0:
            raise ValueError("recent_8bar_density must be within 0..1")
        if self.bars_since_major_statement < 0:
            raise ValueError("bars_since_major_statement may not be negative")
        if (
            self.next_form_boundary_distance_bars is not None
            and self.next_form_boundary_distance_bars < 0
        ):
            raise ValueError("next_form_boundary_distance_bars may not be negative")


def chorus_gesture_adjustment(
    gesture: DrumGesture,
    memory: BebopChorusMemory,
) -> tuple[float, tuple[tuple[str, float], ...]]:
    """Bias one current gesture from drummer-local chorus-scale history."""
    gesture.validate()
    memory.validate()
    score = 0.0
    parts: list[tuple[str, float]] = []

    active = gesture.role in {
        GestureRole.COMP,
        GestureRole.SETUP,
        GestureRole.ACCENT,
        GestureRole.FILL,
    }

    if memory.need_to_back_off:
        if gesture.role is GestureRole.SPACE:
            score += 0.34
            parts.append(("chorus_back_off_space", 0.34))
        elif active:
            score -= 0.34
            parts.append(("chorus_back_off_activity", -0.34))

    if memory.recent_8bar_density >= 0.62:
        if gesture.role is GestureRole.SPACE:
            v = 0.22 * memory.recent_8bar_density
            score += v
            parts.append(("recent_8bar_density_space", v))
        elif active:
            v = -0.28 * memory.recent_8bar_density
            score += v
            parts.append(("recent_8bar_density_activity", v))

    if memory.climax_already_supported:
        if gesture.role is GestureRole.SPACE:
            score += 0.12
            parts.append(("post_climax_headroom", 0.12))
        elif gesture.role is GestureRole.ACCENT:
            score -= 0.16
            parts.append(("avoid_reclimax", -0.16))

    distance = memory.next_form_boundary_distance_bars
    if distance is not None and distance <= 2.0:
        if gesture.role is GestureRole.SETUP:
            v = 0.26 if distance <= 1.0 else 0.14
            score += v
            parts.append(("approaching_form_boundary", v))
        elif gesture.role is GestureRole.SPACE and distance > 1.0:
            score += 0.06
            parts.append(("preserve_setup_headroom", 0.06))

    return score, tuple(parts)
