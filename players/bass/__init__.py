"""AI Bassist instrument-specific realization layer."""

from .interaction_grammar import (
    BassInteractionContext,
    BassInteractionDecision,
    BassInteractionIntent,
    choose_bass_interaction_intent,
)
from .phrase_intent import (
    BassPhraseContext,
    BassPhraseDirection,
    BassPhraseIntent,
    BassPhraseIntentKind,
    BassPhraseState,
    choose_bass_phrase_intent,
)
from .performance_expression import (
    BassExpressionProfile,
    realize_bass_expression,
)
from .partial_written_part_profile import (
    BassFeatureMeasurement,
    PartialBassComparison,
    PartialBassLineProfile,
    compare_partial_bass_profiles,
    full_profile_as_partial,
)
from .practice_curriculum import (
    BassPracticeEvaluation,
    BassPracticeExercise,
    BassPracticeLevel,
    bebop_walking_practice_curriculum,
    curriculum_feature_weights,
)
from .scorebook_evidence import (
    BassScoreEvidenceDirective,
    BassWrittenPartPrior,
    derive_bass_score_context,
    derive_bass_score_evidence,
    evidence_candidate_score,
)
from .scorebook_study import (
    BassScorebookStudyDecision,
    BassScorebookStudyTrack,
    classify_scorebook_bass_study,
)
from .scorebook_practice import (
    BassPracticeMetrics as ScorebookBassPracticeMetrics,
    BassPracticePassResult,
    BassPracticePulse,
    BassPracticeSession,
    BassPracticeSong,
    evaluate_practice_results,
    run_scorebook_practice,
)
from .written_part_measurement import (
    StructuredBassNote,
    measure_written_bass_part,
)
from .written_part_evidence import (
    MeasuredWrittenPartEvidence,
    WrittenPartMeasurementStatus,
    promote_written_part_prior,
)
from .written_part_comparator import (
    BassLineAbstractProfile,
    BassLineComparison,
    BassLineObservation,
    analyze_bass_line,
    compare_bass_lines,
    written_part_prior_from_profile,
)
from .sequential_runner import (
    BassSequentialRunner,
    BassStepInput,
    BassStepResult,
)
from .render_projection import (
    BassRenderEvent,
    project_bass_candidate_to_render_event,
)
from .performance_memory import (
    BassArticulation,
    BassCommittedAction,
    BassPerformanceMemory,
    BassPerformanceSnapshot,
)

from .performance_grammar import (
    ArticulationIntent,
    BassGrammarContext,
    BassGrammarDecision,
    GrooveRelation,
    MetricRole,
    MotionStrategy,
    RegisterIntent,
    TargetStrategy,
    evaluate_bass_grammar,
    metric_role,
)
from .immediate_realizer import (
    BassActionCandidate,
    BassContext,
    BassHarmonicRole,
    BassMode,
    choose_immediate_bass_action,
    generate_immediate_bass_candidates,
)

__all__ = [
    "BassArticulation",
    "BassCommittedAction",
    "BassInteractionContext",
    "BassInteractionDecision",
    "BassExpressionProfile",
    "BassInteractionIntent",
    "BassPerformanceMemory",
    "BassPerformanceSnapshot",
    "BassPracticeEvaluation",
    "BassPracticeExercise",
    "BassPracticeLevel",
    "BassPhraseContext",
    "BassPhraseDirection",
    "BassPhraseIntent",
    "BassPhraseIntentKind",
    "BassPhraseState",
    "BassScoreEvidenceDirective",
    "BassScorebookStudyDecision",
    "BassScorebookStudyTrack",
    "BassWrittenPartPrior",
    "BassFeatureMeasurement",
    "BassLineAbstractProfile",
    "BassLineComparison",
    "BassLineObservation",
    "PartialBassComparison",
    "PartialBassLineProfile",
    "MeasuredWrittenPartEvidence",
    "StructuredBassNote",
    "WrittenPartMeasurementStatus",
    "BassPracticePassResult",
    "BassPracticePulse",
    "BassPracticeSession",
    "BassPracticeSong",
    "BassRenderEvent",
    "BassSequentialRunner",
    "BassStepInput",
    "BassStepResult",
    "ArticulationIntent",
    "BassActionCandidate",
    "BassContext",
    "BassGrammarContext",
    "BassGrammarDecision",
    "BassHarmonicRole",
    "BassMode",
    "GrooveRelation",
    "MetricRole",
    "MotionStrategy",
    "RegisterIntent",
    "TargetStrategy",
    "bebop_walking_practice_curriculum",
    "analyze_bass_line",
    "choose_bass_interaction_intent",
    "choose_bass_phrase_intent",
    "classify_scorebook_bass_study",
    "compare_bass_lines",
    "compare_partial_bass_profiles",
    "choose_immediate_bass_action",
    "curriculum_feature_weights",
    "derive_bass_score_context",
    "derive_bass_score_evidence",
    "evidence_candidate_score",
    "evaluate_practice_results",
    "evaluate_bass_grammar",
    "generate_immediate_bass_candidates",
    "realize_bass_expression",
    "project_bass_candidate_to_render_event",
    "full_profile_as_partial",
    "measure_written_bass_part",
    "promote_written_part_prior",
    "run_scorebook_practice",
    "written_part_prior_from_profile",
    "metric_role",
]
