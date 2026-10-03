"""Audio Evidence Engine public API."""
from .adapters.performance_evidence import (
    PERFORMANCE_EVIDENCE_VERSION,
    to_performance_evidence_payload,
)
from .adapters.source import AudioSource
from .calibration.ambiguity import AmbiguitySummary, summarize_instrument_ambiguity
from .calibration.attribution_comparison import (
    AttributionComparison,
    AttributionSystemSummary,
    compare_instrument_attribution,
)
from .calibration.confidence import ConfidenceReport, confidence_report
from .context.models import ContextEvidence
from .observation.models import (
    AudioObservation,
    DetectorEvidence,
    SeparationMetadata,
)
from .pipeline import AudioEvidencePipeline
from .separated_pipeline import SeparatedAudioEvidencePipeline
from .posterior.fusion import (
    AppliedContextFactor,
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
    "AppliedContextFactor",
    "AttributionComparison",
    "AttributionSystemSummary",
    "AudioEvidencePipeline",
    "AudioObservation",
    "AudioSource",
    "AmbiguitySummary",
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
    "SeparatedAudioEvidencePipeline",
    "compare_instrument_attribution",
    "confidence_report",
    "summarize_instrument_ambiguity",
    "to_performance_evidence_payload",
]
