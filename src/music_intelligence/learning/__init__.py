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
from .style import build_style_artifact
from .genre import build_genre_artifact
from .groove import build_groove_artifact
from .store import LearningStore
from .engine import LearningFeedback,LearningPriorView,SharedLearningEngine
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
    "build_style_artifact",
    "build_genre_artifact",
    "build_groove_artifact",
    "LearningStore",
    "LearningFeedback",
    "LearningPriorView",
    "SharedLearningEngine",
]
