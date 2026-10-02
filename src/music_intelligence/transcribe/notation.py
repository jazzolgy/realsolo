"""Notation intent and candidate representations.

These structures are downstream of performed evidence and upstream of engraving.
They describe *possible readable representations* without mutating or replacing
the original performance events.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import Mapping


class NotationRelevance(str, Enum):
    INCLUDE = "include"
    OMIT = "omit"
    OPTIONAL = "optional"


class NotatedAtomKind(str, Enum):
    NOTE = "note"
    REST = "rest"


@dataclass(frozen=True)
class TupletRatio:
    """Written N-in-the-time-of-M relationship; arbitrary positive N:M."""

    actual: int
    normal: int

    def validate(self) -> None:
        if self.actual <= 0 or self.normal <= 0:
            raise ValueError("tuplet ratio values must be positive")
        if self.actual == self.normal:
            raise ValueError("tuplet ratio must describe a non-trivial ratio")


@dataclass(frozen=True)
class ScoreSpan:
    """Exact score-time span in quarter-note beat units."""

    onset: Fraction
    duration: Fraction

    def validate(self) -> None:
        if self.onset < 0:
            raise ValueError("score onset may not be negative")
        if self.duration <= 0:
            raise ValueError("score duration must be positive")

    @property
    def offset(self) -> Fraction:
        return self.onset + self.duration


@dataclass(frozen=True)
class NotationIntent:
    """Musical interpretation that should guide notation candidate generation."""

    intent_id: str
    source_event_ids: tuple[str, ...]
    relevance: NotationRelevance = NotationRelevance.INCLUDE

    gesture_id: str | None = None
    phrase_context_id: str | None = None
    harmonic_context_id: str | None = None

    preserve_as_single_gesture: bool = False
    prefer_simple_rhythm: bool = True
    allow_tuplet: bool = True
    allow_tie: bool = True
    allow_rest_insertion: bool = True
    articulation_intent: tuple[str, ...] = ()
    technique_intent: tuple[str, ...] = ()

    confidence: float | None = None
    alternatives: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.intent_id:
            raise ValueError("intent_id is required")
        if not self.source_event_ids:
            raise ValueError("NotationIntent requires at least one source event")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("intent confidence must be within 0..1")


@dataclass(frozen=True)
class NotatedAtom:
    """Rhythmic notation atom before pitch spelling / staff allocation."""

    kind: NotatedAtomKind
    span: ScoreSpan
    source_event_ids: tuple[str, ...] = ()
    tie_from_previous: bool = False
    tie_to_next: bool = False
    tuplet: TupletRatio | None = None

    def validate(self) -> None:
        self.span.validate()
        if self.kind is NotatedAtomKind.NOTE and not self.source_event_ids:
            raise ValueError("note atom requires source_event_ids")
        if self.kind is NotatedAtomKind.REST and self.source_event_ids:
            raise ValueError("rest atom may not own performance events")
        if self.kind is NotatedAtomKind.REST and (
            self.tie_from_previous or self.tie_to_next
        ):
            raise ValueError("rests may not carry ties")
        if self.tuplet is not None:
            self.tuplet.validate()


@dataclass(frozen=True)
class NotationCandidate:
    """One readable score interpretation of a NotationIntent."""

    candidate_id: str
    intent_id: str
    atoms: tuple[NotatedAtom, ...]

    fidelity_cost: float = 0.0
    readability_cost: float = 0.0
    complexity_cost: float = 0.0
    confidence: float | None = None
    reasons: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.intent_id:
            raise ValueError("intent_id is required")
        if not self.atoms:
            raise ValueError("candidate requires notation atoms")
        for atom in self.atoms:
            atom.validate()
        for value, name in (
            (self.fidelity_cost, "fidelity_cost"),
            (self.readability_cost, "readability_cost"),
            (self.complexity_cost, "complexity_cost"),
        ):
            if value < 0:
                raise ValueError(f"{name} may not be negative")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("candidate confidence must be within 0..1")

    @property
    def total_cost(self) -> float:
        return self.fidelity_cost + self.readability_cost + self.complexity_cost


def choose_preferred_candidate(
    candidates: tuple[NotationCandidate, ...],
    *,
    fidelity_weight: float = 1.0,
    readability_weight: float = 1.0,
    complexity_weight: float = 1.0,
) -> NotationCandidate:
    """Choose lowest-cost candidate without discarding the alternatives."""

    if not candidates:
        raise ValueError("at least one notation candidate is required")
    for candidate in candidates:
        candidate.validate()

    def score(candidate: NotationCandidate) -> tuple[float, float, str]:
        weighted = (
            fidelity_weight * candidate.fidelity_cost
            + readability_weight * candidate.readability_cost
            + complexity_weight * candidate.complexity_cost
        )
        confidence_tiebreak = -(candidate.confidence or 0.0)
        return weighted, confidence_tiebreak, candidate.candidate_id

    return min(candidates, key=score)
