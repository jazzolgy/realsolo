"""Renderer-neutral layout decisions downstream of engraving semantics.

Important separation learned from professional notation systems:
- magnetic collision avoidance repositions attached objects;
- note spacing changes horizontal music spacing;
- staff optimization changes vertical staff spacing;
- notehead displacement and accidental packing are local collision decisions;
- grace-note spacing is independent from principal-note duration.

None of these operations may rewrite logical score semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from .engraving import EngravingPlan, StemDirection
from .score import GraceNoteKind, ReadableScore, ScoreEvent


class LayoutActionKind(str, Enum):
    MAGNETIC_REPOSITION = "magnetic_reposition"
    HORIZONTAL_RESPACING = "horizontal_respacing"
    STAFF_SPACING_OPTIMIZE = "staff_spacing_optimize"
    NOTEHEAD_DISPLACE = "notehead_displace"
    ACCIDENTAL_COLUMN_PACK = "accidental_column_pack"
    GRACE_NOTE_RESPACING = "grace_note_respacing"
    MANUAL_REVIEW = "manual_review"


class HorizontalSide(str, Enum):
    NONE = "none"
    LEFT = "left"
    RIGHT = "right"


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
class NoteheadDisplacementDecision:
    event_id: str
    side: HorizontalSide
    reason: str

    def validate(self) -> None:
        if not self.event_id:
            raise ValueError("notehead displacement requires event_id")


@dataclass(frozen=True)
class AccidentalColumnDecision:
    event_id: str
    column: int

    def validate(self) -> None:
        if not self.event_id:
            raise ValueError("accidental column requires event_id")
        if self.column < 0:
            raise ValueError("accidental column may not be negative")


@dataclass(frozen=True)
class GraceSpacingDecision:
    event_id: str
    spacing_weight: float
    attach_to_following_event_id: str | None = None

    def validate(self) -> None:
        if not self.event_id:
            raise ValueError("grace spacing requires event_id")
        if self.spacing_weight <= 0:
            raise ValueError("grace spacing weight must be positive")


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


def _staff_position(event: ScoreEvent) -> int | None:
    pitch = event.written_pitch
    if pitch is None:
        return None
    step_index = {"C": 0, "D": 1, "E": 2, "F": 3, "G": 4, "A": 5, "B": 6}[pitch.step]
    return pitch.octave * 7 + step_index


def notehead_displacements(
    score: ReadableScore,
    plan: EngravingPlan,
) -> tuple[NoteheadDisplacementDecision, ...]:
    """Separate simultaneous voices at unison/second collisions.

    The result chooses a horizontal side only; exact x-offsets remain
    renderer-specific.
    """

    score.validate()
    plan.validate(score)
    by_slot: dict[tuple[str, Fraction], list[ScoreEvent]] = {}
    for part in score.parts:
        for event in part.events:
            if event.written_pitch is None:
                continue
            by_slot.setdefault((event.staff_id, event.span.onset), []).append(event)

    out: list[NoteheadDisplacementDecision] = []
    for simultaneous in by_slot.values():
        for i, event in enumerate(simultaneous):
            pos = _staff_position(event)
            if pos is None:
                continue
            for other in simultaneous[i + 1:]:
                other_pos = _staff_position(other)
                if other_pos is None or event.voice_id == other.voice_id:
                    continue
                if abs(pos - other_pos) > 1:
                    continue

                event_intent = plan.for_event(event.event_id)
                other_intent = plan.for_event(other.event_id)
                event_stem = (
                    event_intent.stem_direction
                    if event_intent is not None
                    else StemDirection.AUTO
                )
                other_stem = (
                    other_intent.stem_direction
                    if other_intent is not None
                    else StemDirection.AUTO
                )

                if event_stem is StemDirection.UP and other_stem is StemDirection.DOWN:
                    first_side, second_side = HorizontalSide.RIGHT, HorizontalSide.LEFT
                elif event_stem is StemDirection.DOWN and other_stem is StemDirection.UP:
                    first_side, second_side = HorizontalSide.LEFT, HorizontalSide.RIGHT
                else:
                    first_side, second_side = HorizontalSide.RIGHT, HorizontalSide.LEFT

                out.append(NoteheadDisplacementDecision(
                    event.event_id,
                    first_side,
                    "simultaneous voices collide at unison or second",
                ))
                out.append(NoteheadDisplacementDecision(
                    other.event_id,
                    second_side,
                    "simultaneous voices collide at unison or second",
                ))

    dedup: dict[str, NoteheadDisplacementDecision] = {}
    for decision in out:
        dedup.setdefault(decision.event_id, decision)
    for decision in dedup.values():
        decision.validate()
    return tuple(dedup.values())


def accidental_columns(
    score: ReadableScore,
) -> tuple[AccidentalColumnDecision, ...]:
    """Pack simultaneous accidentals into renderer-neutral columns."""

    score.validate()
    by_slot: dict[tuple[str, Fraction], list[ScoreEvent]] = {}
    for part in score.parts:
        for event in part.events:
            if event.written_pitch is None or event.written_pitch.alter == 0:
                continue
            by_slot.setdefault((event.staff_id, event.span.onset), []).append(event)

    out: list[AccidentalColumnDecision] = []
    for simultaneous in by_slot.values():
        simultaneous.sort(
            key=lambda e: (_staff_position(e) if _staff_position(e) is not None else -999),
            reverse=True,
        )
        columns: list[list[int]] = []
        for event in simultaneous:
            pos = _staff_position(event)
            if pos is None:
                continue
            assigned = None
            for column_index, positions in enumerate(columns):
                if all(abs(pos - existing) >= 3 for existing in positions):
                    assigned = column_index
                    positions.append(pos)
                    break
            if assigned is None:
                assigned = len(columns)
                columns.append([pos])
            decision = AccidentalColumnDecision(event.event_id, assigned)
            decision.validate()
            out.append(decision)
    return tuple(out)


def grace_spacing_decisions(
    score: ReadableScore,
) -> tuple[GraceSpacingDecision, ...]:
    """Keep grace spacing independent from principal-note duration."""

    score.validate()
    out: list[GraceSpacingDecision] = []
    for part in score.parts:
        events = list(part.events)
        for index, event in enumerate(events):
            if event.grace_kind is None:
                continue
            following = next(
                (
                    e for e in events[index + 1:]
                    if e.staff_id == event.staff_id
                    and e.voice_id == event.voice_id
                    and e.grace_kind is None
                    and e.span.onset >= event.span.onset
                ),
                None,
            )
            weight = .58 if event.grace_kind is GraceNoteKind.ACCIACCATURA else .68
            decision = GraceSpacingDecision(
                event.event_id,
                spacing_weight=weight,
                attach_to_following_event_id=following.event_id if following else None,
            )
            decision.validate()
            out.append(decision)
    return tuple(out)


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

    for decision in notehead_displacements(score, plan):
        action = LayoutAction(
            decision.event_id,
            LayoutActionKind.NOTEHEAD_DISPLACE,
            1.0,
            (decision.reason,),
        )
        action.validate()
        actions.append(action)

    for decision in accidental_columns(score):
        if decision.column > 0:
            action = LayoutAction(
                decision.event_id,
                LayoutActionKind.ACCIDENTAL_COLUMN_PACK,
                float(decision.column),
                ("simultaneous accidental moved to an additional column",),
            )
            action.validate()
            actions.append(action)

    for decision in grace_spacing_decisions(score):
        action = LayoutAction(
            decision.event_id,
            LayoutActionKind.GRACE_NOTE_RESPACING,
            max(.01, 1.0 - decision.spacing_weight),
            ("grace note uses reduced spacing independent of principal duration",),
        )
        action.validate()
        actions.append(action)

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

        if (
            pressure.horizontal_pressure
            and plan.profile.optical_note_spacing
            and plan.profile.auto_respace
        ):
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
    grace = {d.event_id: d for d in grace_spacing_decisions(score)}
    decisions: list[OpticalSpacingDecision] = []

    for pressure in pressures:
        intent = intents.get(pressure.event_id)
        base = intent.horizontal_spacing_weight if intent is not None else 1.0
        if pressure.event_id in grace:
            base *= grace[pressure.event_id].spacing_weight
        horizontal = (
            pressure.horizontal_pressure
            if plan.profile.optical_note_spacing and plan.profile.auto_respace
            else 0.0
        )
        reasons: list[str] = []
        if pressure.accidental_pressure:
            reasons.append("accidental needs horizontal clearance")
        if pressure.tuplet_pressure:
            reasons.append("tuplet may need horizontal clearance")
        if pressure.voice_collision_pressure:
            reasons.append("simultaneous voices may need horizontal separation")
        if pressure.cross_staff_pressure:
            reasons.append("cross-staff notation may need horizontal clearance")
        if pressure.event_id in grace:
            reasons.append("grace note receives reduced base spacing")

        decision = OpticalSpacingDecision(
            event_id=pressure.event_id,
            spacing_weight=max(.25, base + horizontal),
            reasons=tuple(reasons),
        )
        decision.validate()
        decisions.append(decision)

    return tuple(decisions)
