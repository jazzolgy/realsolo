"""Engraving intent separated from logical notation semantics.

Sibelius-style engraving decisions such as stem direction, beaming,
cross-staff positioning and optical spacing belong here rather than in the
logical score event.  The same logical score can therefore be rendered under
multiple engraving profiles without changing musical meaning.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import Mapping

from .score import ReadableScore, ScoreEvent


class StemDirection(str, Enum):
    AUTO = "auto"
    UP = "up"
    DOWN = "down"
    NONE = "none"


class BeamState(str, Enum):
    NONE = "none"
    BEGIN = "begin"
    CONTINUE = "continue"
    END = "end"


class PrimaryBeamSide(str, Enum):
    AUTO = "auto"
    FIRST_NOTE = "first_note"
    LAST_NOTE = "last_note"


class TupletBracketMode(str, Enum):
    AUTO = "auto"
    SHOW = "show"
    HIDE = "hide"


class VerticalPlacement(str, Enum):
    AUTO = "auto"
    ABOVE = "above"
    BELOW = "below"


class TiePositionMode(str, Enum):
    OPTICAL = "optical"
    MANUAL = "manual"


@dataclass(frozen=True)
class EngravingProfile:
    """Global house-style-like engraving preferences."""

    optical_note_spacing: bool = True
    auto_respace: bool = True
    magnetic_layout: bool = True
    tie_position_mode: TiePositionMode = TiePositionMode.OPTICAL
    tie_height_scale: float = 1.0
    apply_voice_position_rules_to_cross_staff: bool = True
    apply_tie_rules_to_cross_staff: bool = True
    avoid_cross_staff_beam_corners: bool = True
    cross_staff_primary_beam_side: PrimaryBeamSide = PrimaryBeamSide.FIRST_NOTE
    hide_cross_staff_bar_rests: bool = True
    separate_tuplets_from_adjacent_notes: bool = False
    position_tuplets_as_if_all_notes_beamed: bool = True
    default_tuplet_bracket: TupletBracketMode = TupletBracketMode.AUTO
    minimum_note_spacing: float = 1.0

    def validate(self) -> None:
        if self.minimum_note_spacing <= 0:
            raise ValueError("minimum_note_spacing must be positive")
        if self.tie_height_scale <= 0:
            raise ValueError("tie_height_scale must be positive")


@dataclass(frozen=True)
class EngravingIntent:
    """Visual/engraving decisions for one logical score event."""

    event_id: str
    stem_direction: StemDirection = StemDirection.AUTO
    beam_state: BeamState = BeamState.NONE
    beam_group_id: str | None = None
    secondary_beam_state: BeamState = BeamState.NONE
    secondary_beam_group_id: str | None = None
    cross_staff_target: str | None = None
    tie_placement: VerticalPlacement = VerticalPlacement.AUTO
    tuplet_placement: VerticalPlacement = VerticalPlacement.AUTO
    tuplet_bracket: TupletBracketMode = TupletBracketMode.AUTO
    horizontal_spacing_weight: float = 1.0
    collision_priority: float = 0.5
    hide_default_bar_rest: bool = False
    reasons: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.event_id:
            raise ValueError("engraving intent requires event_id")
        if self.beam_state is BeamState.NONE and self.beam_group_id is not None:
            raise ValueError("beam_group_id requires a non-NONE beam state")
        if self.beam_state is not BeamState.NONE and not self.beam_group_id:
            raise ValueError("beamed event requires beam_group_id")
        if (
            self.secondary_beam_state is BeamState.NONE
            and self.secondary_beam_group_id is not None
        ):
            raise ValueError("secondary_beam_group_id requires a non-NONE state")
        if (
            self.secondary_beam_state is not BeamState.NONE
            and not self.secondary_beam_group_id
        ):
            raise ValueError("secondary beamed event requires group id")
        if self.horizontal_spacing_weight <= 0:
            raise ValueError("horizontal_spacing_weight must be positive")
        if not 0.0 <= self.collision_priority <= 1.0:
            raise ValueError("collision_priority must be within 0..1")


@dataclass(frozen=True)
class EngravingPlan:
    score_id: str
    profile: EngravingProfile = EngravingProfile()
    intents: tuple[EngravingIntent, ...] = ()

    def validate(self, score: ReadableScore | None = None) -> None:
        if not self.score_id:
            raise ValueError("engraving plan requires score_id")
        self.profile.validate()
        ids: set[str] = set()
        for intent in self.intents:
            intent.validate()
            if intent.event_id in ids:
                raise ValueError("duplicate engraving intent for event")
            ids.add(intent.event_id)
        if score is not None:
            score.validate()
            if score.score_id != self.score_id:
                raise ValueError("engraving plan belongs to another score")
            score_ids = {
                event.event_id
                for part in score.parts
                for event in part.events
            }
            unknown = ids - score_ids
            if unknown:
                raise ValueError(f"engraving plan references unknown events: {sorted(unknown)}")

    def for_event(self, event_id: str) -> EngravingIntent | None:
        for intent in self.intents:
            if intent.event_id == event_id:
                return intent
        return None


def voice_stem_directions(events: tuple[ScoreEvent, ...]) -> dict[str, StemDirection]:
    """Assign conventional opposing stems only when independent voices overlap.

    This is engraving logic, not musical voice inference.  Existing voice_ids
    are treated as already-decided logical voices.
    """

    by_staff_onset: dict[tuple[str, Fraction], list[ScoreEvent]] = {}
    for event in events:
        by_staff_onset.setdefault((event.staff_id, event.span.onset), []).append(event)

    directions: dict[str, StemDirection] = {}
    for simultaneous in by_staff_onset.values():
        voices = sorted({event.voice_id for event in simultaneous})
        if len(voices) <= 1:
            for event in simultaneous:
                directions.setdefault(event.event_id, StemDirection.AUTO)
            continue

        # Stable convention: first logical voice up, second down. Additional
        # voices alternate rather than changing their musical identity.
        voice_direction = {
            voice: (StemDirection.UP if index % 2 == 0 else StemDirection.DOWN)
            for index, voice in enumerate(voices)
        }
        for event in simultaneous:
            directions[event.event_id] = voice_direction[event.voice_id]

    return directions


def meter_beam_group(
    meter_numerator: int,
    meter_denominator: int,
) -> Fraction:
    """Return the default primary beam grouping in quarter-note units.

    Verified Sibelius-style defaults:
    - 2/4 and 4/4: eighth notes beam in groups of four;
    - 2/2: four eighths form one half-note beat;
    - 6/8, 9/8, 12/8: dotted-quarter compound beats.

    Other meters fall back to the written beat unit until an explicit grouping
    profile is supplied.
    """

    if meter_numerator <= 0 or meter_denominator <= 0:
        raise ValueError("meter must be positive")

    if meter_denominator == 4 and meter_numerator in {2, 4}:
        return Fraction(2, 1)
    if meter_denominator == 2 and meter_numerator == 2:
        return Fraction(2, 1)

    written_beat = Fraction(4, meter_denominator)
    if meter_denominator == 8 and meter_numerator in {6, 9, 12}:
        return 3 * written_beat
    return written_beat


def beam_group_intents(
    events: tuple[ScoreEvent, ...],
    *,
    beat_group: Fraction = Fraction(1, 1),
    separate_tuplets_from_adjacent_notes: bool = False,
    break_on_rhythm_change: bool = True,
) -> dict[str, tuple[BeamState, str | None]]:
    """Group short notes by written meter and rhythmic shape."""

    if beat_group <= 0:
        raise ValueError("beat_group must be positive")

    buckets: dict[tuple[str, str, int], list[ScoreEvent]] = {}
    for event in events:
        if event.span.duration > Fraction(1, 2):
            continue
        bucket = int(event.span.onset // beat_group)
        buckets.setdefault((event.staff_id, event.voice_id, bucket), []).append(event)

    result: dict[str, tuple[BeamState, str | None]] = {
        event.event_id: (BeamState.NONE, None) for event in events
    }

    for (staff_id, voice_id, bucket), bucket_events in buckets.items():
        bucket_events.sort(key=lambda e: (e.span.onset, e.event_id))
        segments: list[list[ScoreEvent]] = []
        current: list[ScoreEvent] = []

        for event in bucket_events:
            if not current:
                current = [event]
                continue

            previous = current[-1]
            contiguous = previous.span.offset == event.span.onset
            rhythm_changed = (
                break_on_rhythm_change
                and previous.span.duration != event.span.duration
            )
            tuplet_boundary = (
                separate_tuplets_from_adjacent_notes
                and (previous.tuplet is None) != (event.tuplet is None)
            )

            if not contiguous or rhythm_changed or tuplet_boundary:
                segments.append(current)
                current = [event]
            else:
                current.append(event)

        if current:
            segments.append(current)

        for segment_index, group in enumerate(segments):
            if len(group) < 2:
                continue
            group_id = f"beam:{staff_id}:{voice_id}:{bucket}:{segment_index}"
            for index, event in enumerate(group):
                if index == 0:
                    state = BeamState.BEGIN
                elif index == len(group) - 1:
                    state = BeamState.END
                else:
                    state = BeamState.CONTINUE
                result[event.event_id] = (state, group_id)

    return result



def secondary_beam_group(
    meter_numerator: int,
    meter_denominator: int,
) -> Fraction:
    """Return the default secondary-beam subgroup in quarter-note units.

    Reference behavior:
    - simple meter: subgroup every two eighth notes (one quarter note);
    - compound meter: subgroup every three eighth notes (dotted quarter).
    """

    if meter_numerator <= 0 or meter_denominator <= 0:
        raise ValueError("meter must be positive")
    if meter_denominator == 8 and meter_numerator in {6, 9, 12}:
        return Fraction(3, 2)
    return Fraction(1, 1)


def secondary_beam_intents(
    events: tuple[ScoreEvent, ...],
    *,
    subgroup: Fraction,
) -> dict[str, tuple[BeamState, str | None]]:
    """Assign beam level 2 to sixteenth-or-shorter notes by rhythmic subgroup."""

    if subgroup <= 0:
        raise ValueError("secondary-beam subgroup must be positive")

    buckets: dict[tuple[str, str, int], list[ScoreEvent]] = {}
    for event in events:
        if event.span.duration > Fraction(1, 4):
            continue
        bucket = int(event.span.onset // subgroup)
        buckets.setdefault((event.staff_id, event.voice_id, bucket), []).append(event)

    result = {event.event_id: (BeamState.NONE, None) for event in events}
    for (staff_id, voice_id, bucket), group in buckets.items():
        group.sort(key=lambda e: (e.span.onset, e.event_id))
        contiguous: list[list[ScoreEvent]] = []
        current: list[ScoreEvent] = []
        for event in group:
            if current and current[-1].span.offset != event.span.onset:
                contiguous.append(current)
                current = []
            current.append(event)
        if current:
            contiguous.append(current)

        for segment_index, segment in enumerate(contiguous):
            if len(segment) < 2:
                continue
            group_id = f"beam2:{staff_id}:{voice_id}:{bucket}:{segment_index}"
            for index, event in enumerate(segment):
                if index == 0:
                    state = BeamState.BEGIN
                elif index == len(segment) - 1:
                    state = BeamState.END
                else:
                    state = BeamState.CONTINUE
                result[event.event_id] = (state, group_id)
    return result

def _midi_like_position(event: ScoreEvent) -> int | None:
    pitch = event.written_pitch
    if pitch is None:
        return None
    natural_pc = {
        "C": 0,
        "D": 2,
        "E": 4,
        "F": 5,
        "G": 7,
        "A": 9,
        "B": 11,
    }[pitch.step]
    return (pitch.octave + 1) * 12 + natural_pc + pitch.alter


def tuplet_group_placement(
    events: tuple[ScoreEvent, ...],
    *,
    position_as_if_all_notes_beamed: bool = True,
) -> dict[str, VerticalPlacement]:
    """Choose one consistent placement for each contiguous tuplet group."""

    groups: list[list[ScoreEvent]] = []
    current: list[ScoreEvent] = []

    for event in sorted(events, key=lambda e: (e.staff_id, e.voice_id, e.span.onset)):
        if event.tuplet is None:
            if current:
                groups.append(current)
                current = []
            continue

        if not current:
            current = [event]
            continue

        previous = current[-1]
        same_context = (
            previous.staff_id == event.staff_id
            and previous.voice_id == event.voice_id
            and previous.tuplet == event.tuplet
            and previous.span.offset == event.span.onset
        )
        if same_context:
            current.append(event)
        else:
            groups.append(current)
            current = [event]

    if current:
        groups.append(current)

    placements: dict[str, VerticalPlacement] = {}
    for group in groups:
        reference = group if position_as_if_all_notes_beamed else group[:1]
        positions = [p for e in reference if (p := _midi_like_position(e)) is not None]
        if not positions:
            placement = VerticalPlacement.AUTO
        else:
            average = sum(positions) / len(positions)
            placement = (
                VerticalPlacement.BELOW
                if average >= 71
                else VerticalPlacement.ABOVE
            )
        for event in group:
            placements[event.event_id] = placement

    return placements



def cross_staff_tie_placement(
    event: ScoreEvent,
    intent: EngravingIntent,
    profile: EngravingProfile,
) -> VerticalPlacement:
    """Apply normal tie-position policy to cross-staff notes when enabled.

    This mirrors the architectural rule that cross-staff ties should use the
    same tie-position system as ordinary notes rather than a separate ad-hoc
    geometry path.
    """

    if not event.tie_from_previous and not event.tie_to_next:
        return VerticalPlacement.AUTO
    if intent.cross_staff_target is None:
        return intent.tie_placement
    if not profile.apply_tie_rules_to_cross_staff:
        return VerticalPlacement.AUTO
    if intent.tie_placement is not VerticalPlacement.AUTO:
        return intent.tie_placement

    # Initial renderer-neutral convention based on logical voice/stem side.
    if intent.stem_direction is StemDirection.UP:
        return VerticalPlacement.BELOW
    if intent.stem_direction is StemDirection.DOWN:
        return VerticalPlacement.ABOVE
    return VerticalPlacement.AUTO


def cross_staff_primary_beam_side(
    events: tuple[ScoreEvent, ...],
    intents: tuple[EngravingIntent, ...],
    profile: EngravingProfile,
) -> PrimaryBeamSide:
    """Choose cross-staff primary-beam side without changing logical staff.

    When the anti-corner rule is enabled, a group containing cross-staff
    notation places the primary beam on the side of the first note.  Exact beam
    slope/stem endpoints remain renderer responsibilities.
    """

    if not events:
        return PrimaryBeamSide.AUTO
    intent_by_id = {intent.event_id: intent for intent in intents}
    has_cross_staff = any(
        intent_by_id.get(event.event_id) is not None
        and intent_by_id[event.event_id].cross_staff_target is not None
        for event in events
    )
    if not has_cross_staff or not profile.avoid_cross_staff_beam_corners:
        return PrimaryBeamSide.AUTO
    return profile.cross_staff_primary_beam_side

def build_default_engraving_plan(
    score: ReadableScore,
    *,
    profile: EngravingProfile = EngravingProfile(),
) -> EngravingPlan:
    """Build a deterministic initial engraving plan from logical score content."""

    score.validate()
    profile.validate()
    all_events = tuple(event for part in score.parts for event in part.events)
    stem_map = voice_stem_directions(all_events)
    beam_map = beam_group_intents(
        all_events,
        beat_group=meter_beam_group(
            score.meter_numerator,
            score.meter_denominator,
        ),
        separate_tuplets_from_adjacent_notes=profile.separate_tuplets_from_adjacent_notes,
    )
    secondary_map = secondary_beam_intents(
        all_events,
        subgroup=secondary_beam_group(
            score.meter_numerator,
            score.meter_denominator,
        ),
    )
    tuplet_placements = tuplet_group_placement(
        all_events,
        position_as_if_all_notes_beamed=profile.position_tuplets_as_if_all_notes_beamed,
    )

    intents: list[EngravingIntent] = []
    for event in all_events:
        beam_state, beam_group_id = beam_map[event.event_id]
        secondary_beam_state, secondary_beam_group_id = secondary_map[event.event_id]
        cross_staff = None
        # Cross-staff movement must be requested explicitly in logical metadata
        # later; the default plan never invents one.
        reasons: list[str] = []
        if stem_map[event.event_id] is not StemDirection.AUTO:
            reasons.append("opposing stems separate simultaneous logical voices")
        if beam_state is not BeamState.NONE:
            reasons.append("beam group follows score-beat grouping")

        intent = EngravingIntent(
            event_id=event.event_id,
            stem_direction=stem_map[event.event_id],
            beam_state=beam_state,
            beam_group_id=beam_group_id,
            secondary_beam_state=secondary_beam_state,
            secondary_beam_group_id=secondary_beam_group_id,
            cross_staff_target=cross_staff,
            tuplet_placement=tuplet_placements.get(
                event.event_id,
                VerticalPlacement.AUTO,
            ),
            tuplet_bracket=profile.default_tuplet_bracket,
            horizontal_spacing_weight=max(
                profile.minimum_note_spacing,
                1.15 if event.tuplet is not None else 1.0,
            ),
            collision_priority=.75 if event.articulations or event.markings else .5,
            reasons=tuple(reasons),
            provenance=("transcribe:engraving-plan:v1",),
        )
        intent.validate()
        intents.append(intent)

    plan = EngravingPlan(score.score_id, profile, tuple(intents))
    plan.validate(score)
    return plan
