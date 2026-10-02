"""Instrument-specific notation directives for already-performed events.

These are engraving/notation policies only.  They never generate musical
content and never duplicate player improvisation grammar.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .events import CommittedPerformanceEvent
from .notation import NotationRelevance


class NoteheadStyle(str, Enum):
    NORMAL = "normal"
    X = "x"
    DIAMOND = "diamond"
    SLASH = "slash"


@dataclass(frozen=True)
class InstrumentNotationDirective:
    source_event_id: str
    relevance: NotationRelevance
    notehead: NoteheadStyle = NoteheadStyle.NORMAL
    parenthesized: bool = False
    markings: tuple[str, ...] = ()
    articulations: tuple[str, ...] = ()
    confidence: float | None = None
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.source_event_id:
            raise ValueError("source_event_id is required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("directive confidence must be within 0..1")


def bass_notation_directive(
    event: CommittedPerformanceEvent,
) -> InstrumentNotationDirective:
    event.validate()
    if "bass" not in event.instrument.lower():
        raise ValueError("bass directive requires a bass instrument")

    techniques = set(event.technique)
    if "dead_note" in techniques or "muted_dead_note" in techniques:
        directive = InstrumentNotationDirective(
            event.event_id,
            NotationRelevance.INCLUDE,
            notehead=NoteheadStyle.X,
            markings=("dead-note",),
            confidence=event.confidence.notation_relevance,
            reasons=("performed dead note is notation-relevant technique",),
        )
    elif "ghost_note" in techniques:
        directive = InstrumentNotationDirective(
            event.event_id,
            NotationRelevance.OPTIONAL,
            parenthesized=True,
            markings=("ghost",),
            confidence=event.confidence.notation_relevance,
            reasons=("ghost bass attack may be shown without promoting resonance/noise to pitch",),
        )
    else:
        directive = InstrumentNotationDirective(
            event.event_id,
            NotationRelevance.INCLUDE,
            articulations=event.articulation,
            confidence=event.confidence.notation_relevance,
        )
    directive.validate()
    return directive


def sax_notation_directive(
    event: CommittedPerformanceEvent,
) -> InstrumentNotationDirective:
    event.validate()
    if "sax" not in event.instrument.lower():
        raise ValueError("sax directive requires a saxophone instrument")

    technique_map = {
        "scoop": "scoop",
        "fall": "falloff",
        "doit": "doit",
        "bend": "bend",
        "vibrato": "vibrato",
        "growl": "growl",
        "subtone": "subtone",
        "altissimo": "altissimo",
    }
    markings = tuple(
        technique_map[t] for t in event.technique if t in technique_map
    )
    # Crucial separation: scoop/fall/bend stay expressive markings by default,
    # not invented chromatic grace notes.  Explicit grace-note evidence remains
    # available through event.ornament.
    if "grace_note" in event.ornament:
        markings += ("grace-note",)

    directive = InstrumentNotationDirective(
        event.event_id,
        NotationRelevance.INCLUDE,
        markings=markings,
        articulations=event.articulation,
        confidence=event.confidence.notation_relevance,
        reasons=("sax expressive pitch motion is encoded as technique unless separately note-intended",),
    )
    directive.validate()
    return directive


def drum_notation_directive(
    event: CommittedPerformanceEvent,
) -> InstrumentNotationDirective:
    event.validate()
    if event.unpitched is None:
        raise ValueError("drum directive requires unpitched event")

    token = event.unpitched.token.lower()
    techniques = set(event.technique)
    notehead = NoteheadStyle.X if any(
        name in token for name in ("cymbal", "hi_hat", "hihat", "ride", "crash")
    ) else NoteheadStyle.NORMAL
    parenthesized = "ghost_note" in techniques or event.unpitched.technique == "ghost"

    markings: list[str] = []
    for technique in event.technique:
        if technique in {"rimshot", "cross_stick", "brush", "choke", "open", "closed"}:
            markings.append(technique.replace("_", "-"))
    if parenthesized:
        markings.append("ghost")

    directive = InstrumentNotationDirective(
        event.event_id,
        NotationRelevance.INCLUDE,
        notehead=notehead,
        parenthesized=parenthesized,
        markings=tuple(markings),
        confidence=event.confidence.notation_relevance,
        reasons=("drum token/technique is retained without synthetic pitched-note semantics",),
    )
    directive.validate()
    return directive
