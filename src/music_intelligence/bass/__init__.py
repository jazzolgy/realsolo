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
    "choose_bass_interaction_intent",
    "choose_immediate_bass_action",
    "evaluate_bass_grammar",
    "generate_immediate_bass_candidates",
    "realize_bass_expression",
    "project_bass_candidate_to_render_event",
    "metric_role",
]
