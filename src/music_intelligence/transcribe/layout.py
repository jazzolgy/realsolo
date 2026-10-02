"""Renderer-neutral layout decisions downstream of engraving semantics.

Important separation learned from professional notation systems:
- magnetic collision avoidance repositions objects within available space;
- note spacing changes horizontal music spacing;
- staff optimization changes vertical staff spacing.

These are separate operations and none may rewrite logical score semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from .engraving import EngravingPlan
from .score import ReadableScore, ScoreEvent


class LayoutActionKind(str, Enum):
    MAGNETIC_REPOSITION = "magnetic_reposition"
    HORIZONTAL_RESPACING = "horizontal_respacing"
    STAFF_SPACING_OPTIMIZE = "staff_spacing_optimize"
    MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True)
class LayoutPressure:
    event_id: str
    accidental_pressure: float = 0.0
    attached_object_pressure: float = 0.0
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
    def horizontal_pressure(self) -> float:
        return (
            self.accidental_pressure
            + self.tuplet_pressure
            + self.voice_collision_pressure
            + self.cross_staff_pressure
        )

    @property
    def magnetic_pressure(self) -> float:
        return self.attached_object_pressure


@dataclass(frozen=True)
class LayoutAction:
    event_id: str
    kind: LayoutActionKind
    strength: float
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.event_id:
            raise ValueError("layout action requires event_id")
        if self.strength <= 0:
            raise ValueError("layout action strength must be positive")


@dataclass(frozen=True)
class OpticalSpacingDecision:
    """Horizontal note-spacing decision only.

    This deliberately excludes Magnetic Layout object displacement.
    """

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
    """Estimate layout pressure without modifying logical notation."""

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
        attached_object_pressure = .12 * min(
            4,
            len(event.articulations) + len(event.markings),
        )
        tuplet_pressure = .20 if event.tuplet is not None else 0.0
        voice_count = voice_counts[(event.staff_id, event.span.onset)]
        voice_collision_pressure = .18 * max(0, voice_count - 1)
        cross_staff_pressure = (
            .22
            if intent is not None and intent.cross_staff_target is not None
            else 0.0
        )

        pressure = LayoutPressure(
            event_id=event.event_id,
            accidental_pressure=accidental_pressure,
            attached_object_pressure=attached_object_pressure,
            tuplet_pressure=tuplet_pressure,
            voice_collision_pressure=voice_collision_pressure,
            cross_staff_pressure=cross_staff_pressure,
        )
        pressure.validate()
        out.append(pressure)

    return tuple(out)


def layout_actions(
    score: ReadableScore,
    plan: EngravingPlan,
) -> tuple[LayoutAction, ...]:
    """Choose renderer-neutral collision/spacing operations by concern."""

    pressures = layout_pressures(score, plan)
    actions: list[LayoutAction] = []

    for pressure in pressures:
        if pressure.magnetic_pressure and plan.profile.magnetic_layout:
            action = LayoutAction(
                pressure.event_id,
                LayoutActionKind.MAGNETIC_REPOSITION,
                pressure.magnetic_pressure,
                ("attached notation objects should move before score spacing changes",),
            )
            action.validate()
            actions.append(action)

        if pressure.horizontal_pressure and plan.profile.optical_note_spacing:
            reasons: list[str] = []
            if pressure.accidental_pressure:
                reasons.append("accidental clearance")
            if pressure.tuplet_pressure:
                reasons.append("tuplet clearance")
            if pressure.voice_collision_pressure:
                reasons.append("simultaneous voice positioning")
            if pressure.cross_staff_pressure:
                reasons.append("cross-staff note positioning")
            action = LayoutAction(
                pressure.event_id,
                LayoutActionKind.HORIZONTAL_RESPACING,
                pressure.horizontal_pressure,
                tuple(reasons),
            )
            action.validate()
            actions.append(action)

        # Dense cross-staff material can also need vertical staff-space
        # optimization. This remains separate from note spacing.
        if (
            pressure.cross_staff_pressure
            and pressure.attached_object_pressure
            and plan.profile.magnetic_layout
        ):
            action = LayoutAction(
                pressure.event_id,
                LayoutActionKind.STAFF_SPACING_OPTIMIZE,
                pressure.cross_staff_pressure + pressure.attached_object_pressure,
                ("cross-staff attached objects may need additional vertical room",),
            )
            action.validate()
            actions.append(action)

    return tuple(actions)


def optical_spacing_decisions(
    score: ReadableScore,
    plan: EngravingPlan,
) -> tuple[OpticalSpacingDecision, ...]:
    """Return horizontal spacing weights only; never Magnetic Layout offsets."""

    pressures = layout_pressures(score, plan)
    intents = {intent.event_id: intent for intent in plan.intents}
    decisions: list[OpticalSpacingDecision] = []

    for pressure in pressures:
        intent = intents.get(pressure.event_id)
        base = intent.horizontal_spacing_weight if intent is not None else 1.0
        horizontal = pressure.horizontal_pressure if plan.profile.optical_note_spacing else 0.0
        reasons: list[str] = []
        if pressure.accidental_pressure:
            reasons.append("accidental needs horizontal clearance")
        if pressure.tuplet_pressure:
            reasons.append("tuplet may need horizontal clearance")
        if pressure.voice_collision_pressure:
            reasons.append("simultaneous voices may need horizontal separation")
        if pressure.cross_staff_pressure:
            reasons.append("cross-staff notation may need horizontal clearance")

        decision = OpticalSpacingDecision(
            event_id=pressure.event_id,
            spacing_weight=max(1.0, base + horizontal),
            reasons=tuple(reasons),
        )
        decision.validate()
        decisions.append(decision)

    return tuple(decisions)
