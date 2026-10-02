from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class SoloArticulation(str, Enum):
    SUSTAIN = "sustain"
    SHORT = "short"
    LEGATO = "legato"
    VIBRATO = "vibrato"
    SUBTONE = "subtone"
    GROWL = "growl"
    SCOOP = "scoop"
    FALL = "fall"
    BREATHY = "breathy"
    ACCENT = "accent"


_ALIASES = {
    "staccato": SoloArticulation.SHORT,
    "stac": SoloArticulation.SHORT,
    "marcato": SoloArticulation.ACCENT,
    "sus": SoloArticulation.SUSTAIN,
    "susvib": SoloArticulation.VIBRATO,
    "vib": SoloArticulation.VIBRATO,
    "subtone": SoloArticulation.SUBTONE,
    "growl": SoloArticulation.GROWL,
    "scoop": SoloArticulation.SCOOP,
    "fall": SoloArticulation.FALL,
    "breath": SoloArticulation.BREATHY,
    "breathy": SoloArticulation.BREATHY,
    "legato": SoloArticulation.LEGATO,
    "accent": SoloArticulation.ACCENT,
}


def canonical_solo_articulations(tags: Iterable[str]) -> tuple[SoloArticulation, ...]:
    """Normalize player-specific tags into renderer-facing solo articulations."""
    found: list[SoloArticulation] = []
    for raw in tags:
        key = raw.strip().lower().replace("-", "_")
        value = _ALIASES.get(key)
        if value is None:
            for name, candidate in _ALIASES.items():
                if name in key:
                    value = candidate
                    break
        if value is not None and value not in found:
            found.append(value)
    if not found:
        found.append(SoloArticulation.SUSTAIN)
    return tuple(found)


@dataclass(frozen=True, slots=True)
class SoloRenderIntent:
    instrument: str
    pitch_midi: int
    velocity: int
    duration_beats: float
    articulation: tuple[SoloArticulation, ...] = (SoloArticulation.SUSTAIN,)
    vibrato_depth: float = 0.0
    vibrato_rate_hz: float = 5.2
    expression: float = 0.75
    breath_noise: float = 0.0
    pitch_bend_cents: float = 0.0

    def validate(self) -> None:
        if self.instrument not in {"tenor_sax", "alto_sax", "baritone_sax", "trumpet"}:
            raise ValueError("unsupported solo instrument")
        if not 0 <= self.pitch_midi <= 127:
            raise ValueError("pitch_midi must be within 0..127")
        if not 1 <= self.velocity <= 127:
            raise ValueError("velocity must be within 1..127")
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")
        for value, name in (
            (self.vibrato_depth, "vibrato_depth"),
            (self.expression, "expression"),
            (self.breath_noise, "breath_noise"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


def choose_sample_family(intent: SoloRenderIntent) -> str:
    """Choose a sample family without changing the musical note decision."""
    intent.validate()
    arts = set(intent.articulation)
    if SoloArticulation.GROWL in arts:
        return "growl"
    if SoloArticulation.SUBTONE in arts:
        return "subtone"
    if SoloArticulation.SHORT in arts or SoloArticulation.ACCENT in arts:
        return "short"
    if SoloArticulation.VIBRATO in arts:
        return "vibrato"
    return "sustain"
