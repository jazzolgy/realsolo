"""AI Pianist instrument layer.

Shared harmony, phrase, ensemble reasoning, sonority semantics, and generic
polyphonic evaluation come from Core. This package owns piano-specific
realization, comping, and interaction policy.
"""

from .policy import (
    PianoActionScore,
    PianoPerformanceState,
    PianoPolicyEvaluator,
    PianoRealizationCandidate,
    perform_one_piano_action,
)
from .comping import (
    CompingActionType,
    InteractionRole,
    PianoCompingCandidate,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingScore,
    PianoCompingState,
    perform_one_comping_action,
)

__all__ = [
    "PianoActionScore",
    "PianoPerformanceState",
    "PianoPolicyEvaluator",
    "PianoRealizationCandidate",
    "perform_one_piano_action",
    "CompingActionType",
    "InteractionRole",
    "PianoCompingCandidate",
    "PianoCompingContext",
    "PianoCompingEvaluator",
    "PianoCompingScore",
    "PianoCompingState",
    "perform_one_comping_action",
]
