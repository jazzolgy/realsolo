"""Audio Evidence Engine public API."""
from .adapters.performance_evidence import (
    PERFORMANCE_EVIDENCE_VERSION,
    to_performance_evidence_payload,
)
from .adapters.source import AudioSource
from .calibration.confidence import ConfidenceReport, confidence_report
from .context.models import ContextEvidence
from .observation.models import (
    AudioObservation,
    DetectorEvidence,
    SeparationMetadata,
)
from .pipeline import AudioEvidencePipeline
from .posterior.fusion import (
    BoundedContextPosterior,
    ContextualAudioHypothesis,
    PosteriorRevision,
)
from .posterior.revision import (
    AttributionRevisionRecord,
    HardExample,
    RevisionLedger,
)

__all__ = [
    "AudioEvidencePipeline",
    "AudioObservation",
    "AudioSource",
    "AttributionRevisionRecord",
    "BoundedContextPosterior",
    "ConfidenceReport",
    "ContextEvidence",
    "ContextualAudioHypothesis",
    "DetectorEvidence",
    "HardExample",
    "PERFORMANCE_EVIDENCE_VERSION",
    "PosteriorRevision",
    "RevisionLedger",
    "SeparationMetadata",
    "confidence_report",
    "to_performance_evidence_payload",
]
