"""AI Pianist instrument layer.

This package consumes shared Music Intelligence Core context but owns piano-specific
performance grammar, voicing, comping, and interaction policy.
"""

from .policy import (
    PianoActionScore,
    PianoPerformanceState,
    PianoPolicyEvaluator,
    PianoVoicingCandidate,
    perform_one_piano_action,
)

__all__ = [
    "PianoActionScore",
    "PianoPerformanceState",
    "PianoPolicyEvaluator",
    "PianoVoicingCandidate",
    "perform_one_piano_action",
]
