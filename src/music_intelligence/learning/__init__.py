"""Shared learning layer for all RealSolo musical domains."""
from .representation import (
    LearningArtifact,
    LearningDomain,
    StructuralPerformanceData,
    StructuralPerformanceEvent,
)
from .extractors import (
    DEFAULT_EXTRACTORS,
    LearningExtractor,
    extract_learning_artifacts,
)
from .pipeline import (
    AudioAnalysisAdapter,
    LearningConversion,
    LearningDisposition,
    convert_audio_to_learning_data,
)

__all__ = [
    "LearningArtifact",
    "LearningDomain",
    "StructuralPerformanceData",
    "StructuralPerformanceEvent",
    "LearningExtractor",
    "DEFAULT_EXTRACTORS",
    "extract_learning_artifacts",
    "AudioAnalysisAdapter",
    "LearningConversion",
    "LearningDisposition",
    "convert_audio_to_learning_data",
]
