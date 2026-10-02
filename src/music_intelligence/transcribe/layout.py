"""Optical layout heuristics downstream of engraving semantics.

This module models *layout pressure*, not musical meaning.  It is inspired by
engraving systems that separate note semantics from collision avoidance and
optical spacing.  Values are renderer-neutral and may later be translated to
Sibelius/Dorico/MusicXML-specific geometry.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .engraving import EngravingPlan
from .score import ReadableScore, ScoreEvent


@dataclass(frozen=True)
class LayoutPressure:
    event_id: str
    base_spacing: float
    accidental_pressure: float = 0.0
    articulation_pressure: float = 0.0
    tuplet_pressure: float = 0.0
    voice_collision_pressure: float = 0.0
    cross_staff_pressure: float = 0.0

    def validate(self) -> None:
        if not self.event_id:
            raise ValueError("layout pressure requires event_id")
        for name, value in self.__dict__.items():
            if name == "event_id":
                continue
            if value < 0:
                raise ValueError(f"{name} may not be negative")

    @property
    def total(self) -> float:
        return (
            self.base_spacing
            + self.accidental_pressure
            + self.articulation_pressure
            + self.tuplet_pressure
            + self.voice_collision_pressure
            + self.cross_staff_pressure
        )


@dataclass(frozen=True)
class OpticalSpacingDecision:
    event_id: str
    spacing_weight: float
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.event_id:
            raise ValueError("spacing decision requires event_id")
        if self.spacing_weight <= 0:
            raise ValueError("spacing_weight must be positive")


def _simultaneous_voice_counts(events: tuple[ScoreEvent, ...]) -> dict[tuple[str, Fraction], int]:
    voices: dict[tuple[str, Fraction], set[str]] = {}
    for event in events:
        voices.setdefault((event.staff_id, event.span.onset), set()).add(event.voice_id)
    return {key: len(value) for key, value in voices.items()}


def layout_pressures(
    score: ReadableScore,
    plan: EngravingPlan,
) -> tuple[LayoutPressure, ...]:
    """Estimate collision/spacing pressure without modifying logical notation."""

    score.validate()
    plan.validate(score)
    events = tuple(event for part in score.parts for event in part.events)
    voice_counts = _simultaneous_voice_counts(events)

    out: list[LayoutPressure] = []
    for event in events:
        intent = plan.for_event(event.event_id)
        accidental_pressure = (
            .18
            if event.written_pitch is not None and event.written_pitch.alter != 0
            else 0.0
        )
        articulation_pressure = .12 * min(3, len(event.articulations) + len(event.markings))
        tuplet_pressure = .20 if event.tuplet is not None else 0.0
        voice_count = voice_counts[(event.staff_id, event.span.onset)]
        voice_collision_pressure = .18 * max(0, voice_count - 1)
        cross_staff_pressure = (
            .22
            if intent is not None and intent.cross_staff_target is not None
            else 0.0
        )
        base = intent.horizontal_spacing_weight if intent is not None else 1.0

        pressure = LayoutPressure(
            event_id=event.event_id,
            base_spacing=base,
            accidental_pressure=accidental_pressure,
            articulation_pressure=articulation_pressure,
            tuplet_pressure=tuplet_pressure,
            voice_collision_pressure=voice_collision_pressure,
            cross_staff_pressure=cross_staff_pressure,
        )
        pressure.validate()
        out.append(pressure)

    return tuple(out)


def optical_spacing_decisions(
    score: ReadableScore,
    plan: EngravingPlan,
) -> tuple[OpticalSpacingDecision, ...]:
    """Translate collision pressure into renderer-neutral optical spacing weights."""

    pressures = layout_pressures(score, plan)
    decisions: list[OpticalSpacingDecision] = []

    for pressure in pressures:
        reasons: list[str] = []
        if pressure.accidental_pressure:
            reasons.append("accidental needs horizontal clearance")
        if pressure.articulation_pressure:
            reasons.append("articulation/marking increases local layout pressure")
        if pressure.tuplet_pressure:
            reasons.append("tuplet requires additional notation clearance")
        if pressure.voice_collision_pressure:
            reasons.append("simultaneous voices require collision separation")
        if pressure.cross_staff_pressure:
            reasons.append("cross-staff notation requires extra collision margin")

        decision = OpticalSpacingDecision(
            event_id=pressure.event_id,
            spacing_weight=max(1.0, pressure.total),
            reasons=tuple(reasons),
        )
        decision.validate()
        decisions.append(decision)

    return tuple(decisions)
