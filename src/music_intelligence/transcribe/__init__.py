"""Standalone-ready transcription / notation contracts.

This package intentionally owns notation-domain contracts only. It must remain
usable without importing RealSolo realtime, Player generation policy, or
ensemble interaction state machines.
"""

from .events import (
    CONTRACT_VERSION as PERFORMANCE_EVIDENCE_CONTRACT_VERSION,
    CommittedPerformanceEvent,
    ConfidenceBundle,
    EventAlternative,
    EvidenceKind,
    EvidenceRef,
    PerformedPitch,
    PerformanceCommitment,
    PerformanceTimeSpan,
    UnpitchedToken,
    event_from_payload,
    event_to_payload,
)
from .notation import (
    CONTRACT_VERSION as NOTATION_CONTRACT_VERSION,
    NotatedAtom,
    NotatedAtomKind,
    NotationCandidate,
    NotationIntent,
    NotationRelevance,
    ScoreSpan,
    TupletRatio,
    choose_preferred_candidate,
    notation_candidate_from_payload,
    notation_candidate_to_payload,
    notation_intent_from_payload,
    notation_intent_to_payload,
)

__all__ = [
    "PERFORMANCE_EVIDENCE_CONTRACT_VERSION",
    "NOTATION_CONTRACT_VERSION",
    "CommittedPerformanceEvent",
    "ConfidenceBundle",
    "EventAlternative",
    "EvidenceKind",
    "EvidenceRef",
    "PerformedPitch",
    "PerformanceCommitment",
    "PerformanceTimeSpan",
    "UnpitchedToken",
    "event_from_payload",
    "event_to_payload",
    "NotatedAtom",
    "NotatedAtomKind",
    "NotationCandidate",
    "NotationIntent",
    "NotationRelevance",
    "ScoreSpan",
    "TupletRatio",
    "choose_preferred_candidate",
    "notation_candidate_from_payload",
    "notation_candidate_to_payload",
    "notation_intent_from_payload",
    "notation_intent_to_payload",
]
