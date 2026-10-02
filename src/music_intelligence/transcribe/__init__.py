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

__all__ = [
    "CommittedPerformanceEvent",
    "ConfidenceBundle",
    "EventAlternative",
    "EvidenceKind",
    "EvidenceRef",
    "PerformedPitch",
    "PerformanceTimeSpan",
    "UnpitchedToken",
]
