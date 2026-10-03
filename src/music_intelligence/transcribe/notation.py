"""Notation intent and candidate contracts.

These structures are downstream of performed evidence and upstream of engraving.
They describe possible readable representations without mutating the original
performance evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import Any, Mapping

CONTRACT_VERSION = "notation-candidate.v1"


class NotationRelevance(str, Enum):
    INCLUDE = "include"
    OMIT = "omit"
    OPTIONAL = "optional"


class NotatedAtomKind(str, Enum):
    NOTE = "note"
    REST = "rest"


@dataclass(frozen=True)
class TupletRatio:
    actual: int
    normal: int

    def validate(self) -> None:
        if self.actual <= 0 or self.normal <= 0:
            raise ValueError("tuplet ratio values must be positive")
        if self.actual == self.normal:
            raise ValueError("tuplet ratio must describe a non-trivial ratio")


@dataclass(frozen=True)
class ScoreSpan:
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


def _fraction_payload(value: Fraction) -> list[int]:
    return [value.numerator, value.denominator]


def _fraction_from_payload(value: Any) -> Fraction:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError("fraction payload must be [numerator, denominator]")
    return Fraction(int(value[0]), int(value[1]))


def notation_intent_to_payload(intent: NotationIntent) -> dict[str, Any]:
    intent.validate()
    return {
        "schema_version": CONTRACT_VERSION,
        "kind": "notation_intent",
        "intent_id": intent.intent_id,
        "source_event_ids": list(intent.source_event_ids),
        "relevance": intent.relevance.value,
        "gesture_id": intent.gesture_id,
        "phrase_context_id": intent.phrase_context_id,
        "harmonic_context_id": intent.harmonic_context_id,
        "preserve_as_single_gesture": intent.preserve_as_single_gesture,
        "prefer_simple_rhythm": intent.prefer_simple_rhythm,
        "allow_tuplet": intent.allow_tuplet,
        "allow_tie": intent.allow_tie,
        "allow_rest_insertion": intent.allow_rest_insertion,
        "articulation_intent": list(intent.articulation_intent),
        "technique_intent": list(intent.technique_intent),
        "confidence": intent.confidence,
        "alternatives": list(intent.alternatives),
        "evidence_ids": list(intent.evidence_ids),
        "provenance": list(intent.provenance),
        "metadata": dict(intent.metadata),
    }


def notation_intent_from_payload(payload: Mapping[str, Any]) -> NotationIntent:
    version = str(payload.get("schema_version", CONTRACT_VERSION))
    if version != CONTRACT_VERSION:
        raise ValueError(f"unsupported notation schema: {version}")
    intent = NotationIntent(
        intent_id=str(payload["intent_id"]),
        source_event_ids=tuple(payload["source_event_ids"]),
        relevance=NotationRelevance(str(payload.get("relevance", "include"))),
        gesture_id=payload.get("gesture_id"),
        phrase_context_id=payload.get("phrase_context_id"),
        harmonic_context_id=payload.get("harmonic_context_id"),
        preserve_as_single_gesture=bool(payload.get("preserve_as_single_gesture", False)),
        prefer_simple_rhythm=bool(payload.get("prefer_simple_rhythm", True)),
        allow_tuplet=bool(payload.get("allow_tuplet", True)),
        allow_tie=bool(payload.get("allow_tie", True)),
        allow_rest_insertion=bool(payload.get("allow_rest_insertion", True)),
        articulation_intent=tuple(payload.get("articulation_intent") or ()),
        technique_intent=tuple(payload.get("technique_intent") or ()),
        confidence=payload.get("confidence"),
        alternatives=tuple(payload.get("alternatives") or ()),
        evidence_ids=tuple(payload.get("evidence_ids") or ()),
        provenance=tuple(payload.get("provenance") or ()),
        metadata=dict(payload.get("metadata") or {}),
    )
    intent.validate()
    return intent


def notation_candidate_to_payload(candidate: NotationCandidate) -> dict[str, Any]:
    candidate.validate()
    return {
        "schema_version": CONTRACT_VERSION,
        "kind": "notation_candidate",
        "candidate_id": candidate.candidate_id,
        "intent_id": candidate.intent_id,
        "atoms": [
            {
                "kind": atom.kind.value,
                "span": {
                    "onset": _fraction_payload(atom.span.onset),
                    "duration": _fraction_payload(atom.span.duration),
                },
                "source_event_ids": list(atom.source_event_ids),
                "tie_from_previous": atom.tie_from_previous,
                "tie_to_next": atom.tie_to_next,
                "tuplet": (
                    {"actual": atom.tuplet.actual, "normal": atom.tuplet.normal}
                    if atom.tuplet
                    else None
                ),
            }
            for atom in candidate.atoms
        ],
        "fidelity_cost": candidate.fidelity_cost,
        "readability_cost": candidate.readability_cost,
        "complexity_cost": candidate.complexity_cost,
        "confidence": candidate.confidence,
        "reasons": list(candidate.reasons),
        "alternatives": list(candidate.alternatives),
        "evidence_ids": list(candidate.evidence_ids),
        "provenance": list(candidate.provenance),
    }


def notation_candidate_from_payload(payload: Mapping[str, Any]) -> NotationCandidate:
    version = str(payload.get("schema_version", CONTRACT_VERSION))
    if version != CONTRACT_VERSION:
        raise ValueError(f"unsupported notation schema: {version}")

    atoms = []
    for raw in payload["atoms"]:
        tuplet_raw = raw.get("tuplet")
        atoms.append(
            NotatedAtom(
                kind=NotatedAtomKind(str(raw["kind"])),
                span=ScoreSpan(
                    onset=_fraction_from_payload(raw["span"]["onset"]),
                    duration=_fraction_from_payload(raw["span"]["duration"]),
                ),
                source_event_ids=tuple(raw.get("source_event_ids") or ()),
                tie_from_previous=bool(raw.get("tie_from_previous", False)),
                tie_to_next=bool(raw.get("tie_to_next", False)),
                tuplet=(
                    TupletRatio(
                        actual=int(tuplet_raw["actual"]),
                        normal=int(tuplet_raw["normal"]),
                    )
                    if tuplet_raw
                    else None
                ),
            )
        )

    candidate = NotationCandidate(
        candidate_id=str(payload["candidate_id"]),
        intent_id=str(payload["intent_id"]),
        atoms=tuple(atoms),
        fidelity_cost=float(payload.get("fidelity_cost", 0.0)),
        readability_cost=float(payload.get("readability_cost", 0.0)),
        complexity_cost=float(payload.get("complexity_cost", 0.0)),
        confidence=payload.get("confidence"),
        reasons=tuple(payload.get("reasons") or ()),
        alternatives=tuple(payload.get("alternatives") or ()),
        evidence_ids=tuple(payload.get("evidence_ids") or ()),
        provenance=tuple(payload.get("provenance") or ()),
    )
    candidate.validate()
    return candidate
