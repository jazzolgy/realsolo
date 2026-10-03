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
from .groove_grammar import GrooveGrammar, DEFAULT_GROOVE_GRAMMARS, best_matching_grammars, groove_similarity
from .store import LearningStore
from .audio_evidence import artifacts_from_audio_aggregate
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
    "GrooveGrammar",
    "DEFAULT_GROOVE_GRAMMARS",
    "best_matching_grammars",
    "groove_similarity",
    "LearningStore",
    "artifacts_from_audio_aggregate",
    "LearningFeedback",
    "LearningPriorView",
    "SharedLearningEngine",
]


from .score_alignment import (
    AlignmentStatus,
    PerformancePhase,
    MusicalScoreCoordinate,
    AudioScoreAlignment,
    ScoreAlignedEvidence,
    same_musical_position,
    same_form_relative_position,
    research_learning_status,
)
__all__ += [
    "AlignmentStatus","PerformancePhase","MusicalScoreCoordinate",
    "AudioScoreAlignment","ScoreAlignedEvidence","same_musical_position",
    "same_form_relative_position","research_learning_status",
]
