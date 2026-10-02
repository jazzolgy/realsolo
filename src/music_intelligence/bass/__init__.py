"""AI Bassist instrument-specific realization layer."""

from .immediate_realizer import (
    BassActionCandidate,
    BassContext,
    BassHarmonicRole,
    BassMode,
    choose_immediate_bass_action,
    generate_immediate_bass_candidates,
)

__all__ = [
    "BassActionCandidate",
    "BassContext",
    "BassHarmonicRole",
    "BassMode",
    "choose_immediate_bass_action",
    "generate_immediate_bass_candidates",
]
