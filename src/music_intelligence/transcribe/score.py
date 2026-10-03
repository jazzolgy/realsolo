"""Readable score assembly model.

This is a notation-domain model, not UMR and not a player performance model.
It is intentionally small enough to feed MusicXML or another engraving adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from .events import MusicalCoordinate, PerceptualDynamics, UnpitchedToken
from .notation import NotatedAtomKind, ScoreSpan, TupletRatio
from .spelling import WrittenPitch


@dataclass(frozen=True)
class ScoreKeySignature:
    fifths: int = 0
    mode: str = "major"

    def validate(self) -> None:
        if not -7 <= self.fifths <= 7:
            raise ValueError("key signature fifths must be within -7..7")
        if not self.mode:
            raise ValueError("key signature mode is required")


@dataclass(frozen=True)
class ScoreTextDirection:
    text: str
    onset: Fraction = Fraction(0)
    placement: str = "above"
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.text.strip():
            raise ValueError("score text direction requires text")
        if self.onset < 0:
            raise ValueError("score text direction onset may not be negative")
        if self.placement not in {"above", "below"}:
            raise ValueError("score text direction placement must be above or below")


class ScoreSpannerKind(str, Enum):
    CRESCENDO = "crescendo"
    DIMINUENDO = "diminuendo"


@dataclass(frozen=True)
class ScoreSpanner:
    spanner_id: str
    kind: ScoreSpannerKind
    part_id: str
    start_event_id: str
    end_event_id: str
    placement: str = "below"
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.spanner_id or not self.part_id:
            raise ValueError("spanner identity is required")
        if not self.start_event_id or not self.end_event_id:
            raise ValueError("spanner endpoints are required")
        if self.start_event_id == self.end_event_id:
            raise ValueError("spanner endpoints must differ")
        if self.placement not in {"above", "below"}:
            raise ValueError("spanner placement must be above or below")


class GraceNoteKind(str, Enum):
    ACCIACCATURA = "acciaccatura"
    APPOGGIATURA = "appoggiatura"
    UNSLASHED = "unslashed"


@dataclass(frozen=True)
class ScoreEvent:
    event_id: str
    part_id: str
    staff_id: str
    voice_id: str
    kind: NotatedAtomKind
    span: ScoreSpan
    source_event_ids: tuple[str, ...] = ()
    written_pitch: WrittenPitch | None = None
    unpitched: UnpitchedToken | None = None
    tie_from_previous: bool = False
    tie_to_next: bool = False
    tuplet: TupletRatio | None = None
    grace_kind: GraceNoteKind | None = None
    simultaneity_group_id: str | None = None
    dynamic_marking: str | None = None
    musical_coordinate: MusicalCoordinate | None = None
    dynamics: PerceptualDynamics | None = None
    articulations: tuple[str, ...] = ()
    markings: tuple[str, ...] = ()
    confidence: float | None = None
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.event_id or not self.part_id or not self.staff_id or not self.voice_id:
            raise ValueError("score event identity fields are required")
        self.span.validate()
        if self.kind is NotatedAtomKind.REST:
            if self.written_pitch is not None or self.unpitched is not None:
                raise ValueError("rest may not carry pitch")
            if self.source_event_ids:
                raise ValueError("rest may not own performance events")
        else:
            if not self.source_event_ids:
                raise ValueError("note requires source event ids")
            if (self.written_pitch is None) == (self.unpitched is None):
                raise ValueError("note requires exactly one pitched/unpitched payload")
            if self.written_pitch is not None:
                self.written_pitch.validate()
            if self.unpitched is not None:
                self.unpitched.validate()
        if self.tuplet is not None:
            self.tuplet.validate()
        if self.grace_kind is not None and self.kind is NotatedAtomKind.REST:
            raise ValueError("rest may not be a grace note")
        if self.simultaneity_group_id is not None:
            if self.kind is NotatedAtomKind.REST:
                raise ValueError("rest may not belong to a simultaneity group")
            if not self.simultaneity_group_id.strip():
                raise ValueError("simultaneity_group_id may not be blank")
        if self.dynamic_marking is not None and not self.dynamic_marking.strip():
            raise ValueError("dynamic_marking may not be blank")
        if self.musical_coordinate is not None:
            self.musical_coordinate.validate()
        if self.dynamics is not None:
            self.dynamics.validate()
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("score-event confidence must be within 0..1")


@dataclass(frozen=True)
class ScorePart:
    part_id: str
    name: str
    instrument: str
    staff_ids: tuple[str, ...]
    events: tuple[ScoreEvent, ...]
    profile_id: str | None = None

    def validate(self) -> None:
        if not self.part_id or not self.name or not self.instrument:
            raise ValueError("score part identity is required")
        if not self.staff_ids:
            raise ValueError("score part requires at least one staff")
        if len(self.staff_ids) != len(set(self.staff_ids)):
            raise ValueError("staff_ids must be unique")
        previous_onset: dict[tuple[str, str], Fraction] = {}
        previous_end: dict[tuple[str, str], Fraction] = {}
        previous_group: dict[tuple[str, str], str | None] = {}
        simultaneity_groups: dict[str, list[ScoreEvent]] = {}
        for event in self.events:
            event.validate()
            if event.part_id != self.part_id:
                raise ValueError("score event belongs to another part")
            if event.staff_id not in self.staff_ids:
                raise ValueError("score event references unknown staff")
            key = (event.staff_id, event.voice_id)
            prior_onset = previous_onset.get(key)
            if prior_onset is not None and event.span.onset < prior_onset:
                raise ValueError("events must be ordered within each staff/voice")

            prior_end = previous_end.get(key)
            prior_group = previous_group.get(key)
            same_chord_group = (
                event.simultaneity_group_id is not None
                and event.simultaneity_group_id == prior_group
                and event.span.onset == prior_onset
            )
            if (
                prior_end is not None
                and event.span.onset < prior_end
                and not same_chord_group
            ):
                raise ValueError(
                    "overlapping events in one staff/voice require distinct "
                    "voices or a simultaneity group"
                )

            previous_onset[key] = event.span.onset
            if event.grace_kind is None:
                previous_end[key] = max(
                    prior_end or event.span.offset,
                    event.span.offset,
                )
            elif prior_end is None:
                previous_end[key] = event.span.onset
            previous_group[key] = event.simultaneity_group_id
            if event.simultaneity_group_id is not None:
                simultaneity_groups.setdefault(
                    event.simultaneity_group_id,
                    [],
                ).append(event)

        for group_id, members in simultaneity_groups.items():
            if len(members) < 2:
                raise ValueError(
                    f"simultaneity group {group_id} requires at least two notes"
                )
            first = members[0]
            expected = (
                first.part_id,
                first.staff_id,
                first.voice_id,
                first.span.onset,
                first.span.duration,
            )
            for member in members[1:]:
                actual = (
                    member.part_id,
                    member.staff_id,
                    member.voice_id,
                    member.span.onset,
                    member.span.duration,
                )
                if actual != expected:
                    raise ValueError(
                        f"simultaneity group {group_id} must share "
                        "part/staff/voice/onset/duration"
                    )


@dataclass(frozen=True)
class ReadableScore:
    score_id: str
    title: str
    parts: tuple[ScorePart, ...]
    spanners: tuple[ScoreSpanner, ...] = ()
    directions: tuple[ScoreTextDirection, ...] = ()
    meter_numerator: int = 4
    meter_denominator: int = 4
    key_signature: ScoreKeySignature = ScoreKeySignature()
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.score_id:
            raise ValueError("score_id is required")
        if self.meter_numerator <= 0 or self.meter_denominator <= 0:
            raise ValueError("meter must be positive")
        self.key_signature.validate()
        if not self.parts:
            raise ValueError("score requires at least one part")
        ids = [p.part_id for p in self.parts]
        if len(ids) != len(set(ids)):
            raise ValueError("part_id values must be unique")
        events_by_id: dict[str, ScoreEvent] = {}
        for part in self.parts:
            part.validate()
            for event in part.events:
                if event.event_id in events_by_id:
                    raise ValueError("score event ids must be unique across parts")
                events_by_id[event.event_id] = event

        for direction in self.directions:
            direction.validate()

        spanner_ids: set[str] = set()
        for spanner in self.spanners:
            spanner.validate()
            if spanner.spanner_id in spanner_ids:
                raise ValueError("spanner ids must be unique")
            spanner_ids.add(spanner.spanner_id)
            start = events_by_id.get(spanner.start_event_id)
            end = events_by_id.get(spanner.end_event_id)
            if start is None or end is None:
                raise ValueError("spanner references unknown event")
            if start.part_id != spanner.part_id or end.part_id != spanner.part_id:
                raise ValueError("spanner endpoints must belong to its part")
            if end.span.onset <= start.span.onset:
                raise ValueError("spanner end must follow start")


def assemble_score(
    *,
    score_id: str,
    title: str,
    parts: tuple[ScorePart, ...],
    spanners: tuple[ScoreSpanner, ...] = (),
    directions: tuple[ScoreTextDirection, ...] = (),
    meter_numerator: int = 4,
    meter_denominator: int = 4,
    key_signature: ScoreKeySignature = ScoreKeySignature(),
    provenance: tuple[str, ...] = (),
) -> ReadableScore:
    score = ReadableScore(
        score_id=score_id,
        title=title,
        parts=parts,
        spanners=spanners,
        directions=directions,
        meter_numerator=meter_numerator,
        meter_denominator=meter_denominator,
        key_signature=key_signature,
        provenance=provenance + ("transcribe:score-assembly",),
    )
    score.validate()
    return score


def extract_individual_part(score: ReadableScore, part_id: str) -> ReadableScore:
    score.validate()
    matches = tuple(p for p in score.parts if p.part_id == part_id)
    if not matches:
        raise ValueError(f"unknown part_id: {part_id}")
    return ReadableScore(
        score_id=f"{score.score_id}:part:{part_id}",
        title=f"{score.title} — {matches[0].name}",
        parts=matches,
        spanners=tuple(s for s in score.spanners if s.part_id == part_id),
        directions=score.directions,
        meter_numerator=score.meter_numerator,
        meter_denominator=score.meter_denominator,
        key_signature=score.key_signature,
        provenance=score.provenance + ("transcribe:individual-part",),
    )


# Explicit terminology for the post-Sibelius engraving split.
# Backward-compatible names remain available while downstream code migrates.
LogicalScoreEvent = ScoreEvent
LogicalScorePart = ScorePart
LogicalScore = ReadableScore


def assemble_logical_score(
    *,
    score_id: str,
    title: str,
    parts: tuple[LogicalScorePart, ...],
    spanners: tuple[ScoreSpanner, ...] = (),
    directions: tuple[ScoreTextDirection, ...] = (),
    meter_numerator: int = 4,
    meter_denominator: int = 4,
    key_signature: ScoreKeySignature = ScoreKeySignature(),
    provenance: tuple[str, ...] = (),
) -> LogicalScore:
    return assemble_score(
        score_id=score_id,
        title=title,
        parts=parts,
        spanners=spanners,
        directions=directions,
        meter_numerator=meter_numerator,
        meter_denominator=meter_denominator,
        key_signature=key_signature,
        provenance=provenance + ("transcribe:logical-score",),
    )
