"""Transcription / notation workstream public API.

This package consumes committed performance evidence and later projects it into
readable notation.  It must not contain player generation policy.
"""

from .events import (
    CommittedPerformanceEvent,
    ConfidenceBundle,
    EventAlternative,
    EvidenceKind,
    EvidenceRef,
    PerformedPitch,
    PerformanceTimeSpan,
    UnpitchedToken,
)
from .notation import (
    NotatedAtom,
    NotatedAtomKind,
    NotationCandidate,
    NotationIntent,
    NotationRelevance,
    ScoreSpan,
    TupletRatio,
    choose_preferred_candidate,
)
from .rhythm import (
    QuantizationGrid,
    quantize_score_span,
    rest_for_gap,
    split_note_across_bars,
    tuplet_note,
)

__all__ = [
    "CommittedPerformanceEvent",
    "ConfidenceBundle",
    "EventAlternative",
    "EvidenceKind",
    "EvidenceRef",
    "PerformedPitch",
    "PerformanceTimeSpan",
    "UnpitchedToken",
    "NotatedAtom",
    "NotatedAtomKind",
    "NotationCandidate",
    "NotationIntent",
    "NotationRelevance",
    "ScoreSpan",
    "TupletRatio",
    "choose_preferred_candidate",
    "QuantizationGrid",
    "quantize_score_span",
    "rest_for_gap",
    "split_note_across_bars",
    "tuplet_note",
]
