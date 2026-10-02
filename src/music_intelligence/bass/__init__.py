"""AI Bassist instrument-specific realization layer."""

from .interaction_grammar import (
    BassInteractionContext,
    BassInteractionDecision,
    BassInteractionIntent,
    choose_bass_interaction_intent,
)
from .performance_expression import (
    BassExpressionProfile,
    realize_bass_expression,
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
    "choose_bass_interaction_intent",
    "choose_immediate_bass_action",
    "evaluate_bass_grammar",
    "generate_immediate_bass_candidates",
    "realize_bass_expression",
    "metric_role",
]
