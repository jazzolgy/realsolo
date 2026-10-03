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


from .product import (
    EventTranscriptionResult,
    PerformanceEvidenceSource,
    TranscriptionNotationConfig,
    TranscriptionNotationEngine,
)

__all__ += [
    "EventTranscriptionResult",
    "PerformanceEvidenceSource",
    "TranscriptionNotationConfig",
    "TranscriptionNotationEngine",
]


from .score import (
    GraceNoteKind,
    LogicalScore,
    LogicalScoreEvent,
    LogicalScorePart,
    ReadableScore,
    ScoreEvent,
    ScoreKeySignature,
    ScorePart,
    ScoreSpanner,
    ScoreSpannerKind,
    assemble_logical_score,
    assemble_score,
    extract_individual_part,
)
from .engraving import (
    EngravingIntent,
    EngravingPlan,
    EngravingProfile,
    build_default_engraving_plan,
)
from .quality import (
    QualityIssueSeverity,
    ScoreQualityIssue,
    ScoreQualityReport,
    audit_score_for_performance,
)
from .musicxml import score_to_musicxml

__all__ += [
    "GraceNoteKind",
    "LogicalScore",
    "LogicalScoreEvent",
    "LogicalScorePart",
    "ReadableScore",
    "ScoreEvent",
    "ScoreKeySignature",
    "ScorePart",
    "ScoreSpanner",
    "ScoreSpannerKind",
    "assemble_logical_score",
    "assemble_score",
    "extract_individual_part",
    "EngravingIntent",
    "EngravingPlan",
    "EngravingProfile",
    "build_default_engraving_plan",
    "QualityIssueSeverity",
    "ScoreQualityIssue",
    "ScoreQualityReport",
    "audit_score_for_performance",
    "score_to_musicxml",
]
