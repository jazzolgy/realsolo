"""Shared Audio Intelligence Engine contracts and first vertical slice."""
from .attribution.fusion import PosteriorAttributor
from .bridge import to_structural_performance_data
from .schemas.evidence import (
    AttributionFactor,
    AttributionRevision,
    AudioEventHypothesis,
    ConfidenceVector,
    EventStatus,
    RevisionRecord,
)
from .self_correction.revision import HardExample, RevisionLedger
from .validation.autumn_leaves import (
    AutumnLeavesValidationCase,
    summarize_validation_events,
)

__all__ = [
    "AttributionFactor",
    "AttributionRevision",
    "AudioEventHypothesis",
    "ConfidenceVector",
    "EventStatus",
    "RevisionRecord",
    "PosteriorAttributor",
    "HardExample",
    "RevisionLedger",
    "to_structural_performance_data",
    "AutumnLeavesValidationCase",
    "summarize_validation_events",
]
