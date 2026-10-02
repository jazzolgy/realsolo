"""Readable score assembly model.

This is a notation-domain model, not UMR and not a player performance model.
It is intentionally small enough to feed MusicXML or another engraving adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from .events import UnpitchedToken
from .notation import NotatedAtomKind, ScoreSpan, TupletRatio
from .spelling import WrittenPitch


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
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("score-event confidence must be within 0..1")


@dataclass(frozen=True)
class ScorePart:
    part_id: str
    name: str
    instrument: str
    staff_ids: tuple[str, ...]
    events: tuple[ScoreEvent, ...]

    def validate(self) -> None:
        if not self.part_id or not self.name or not self.instrument:
            raise ValueError("score part identity is required")
        if not self.staff_ids:
            raise ValueError("score part requires at least one staff")
        if len(self.staff_ids) != len(set(self.staff_ids)):
            raise ValueError("staff_ids must be unique")
        previous: dict[tuple[str, str], Fraction] = {}
        for event in self.events:
            event.validate()
            if event.part_id != self.part_id:
                raise ValueError("score event belongs to another part")
            if event.staff_id not in self.staff_ids:
                raise ValueError("score event references unknown staff")
            key = (event.staff_id, event.voice_id)
            prior = previous.get(key)
            if prior is not None and event.span.onset < prior:
                raise ValueError("events must be ordered within each staff/voice")
            previous[key] = event.span.onset


@dataclass(frozen=True)
class ReadableScore:
    score_id: str
    title: str
    parts: tuple[ScorePart, ...]
    meter_numerator: int = 4
    meter_denominator: int = 4
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.score_id:
            raise ValueError("score_id is required")
        if self.meter_numerator <= 0 or self.meter_denominator <= 0:
            raise ValueError("meter must be positive")
        if not self.parts:
            raise ValueError("score requires at least one part")
        ids = [p.part_id for p in self.parts]
        if len(ids) != len(set(ids)):
            raise ValueError("part_id values must be unique")
        for part in self.parts:
            part.validate()


def assemble_score(
    *,
    score_id: str,
    title: str,
    parts: tuple[ScorePart, ...],
    meter_numerator: int = 4,
    meter_denominator: int = 4,
    provenance: tuple[str, ...] = (),
) -> ReadableScore:
    score = ReadableScore(
        score_id=score_id,
        title=title,
        parts=parts,
        meter_numerator=meter_numerator,
        meter_denominator=meter_denominator,
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
        meter_numerator=score.meter_numerator,
        meter_denominator=score.meter_denominator,
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
    meter_numerator: int = 4,
    meter_denominator: int = 4,
    provenance: tuple[str, ...] = (),
) -> LogicalScore:
    return assemble_score(
        score_id=score_id,
        title=title,
        parts=parts,
        meter_numerator=meter_numerator,
        meter_denominator=meter_denominator,
        provenance=provenance + ("transcribe:logical-score",),
    )
