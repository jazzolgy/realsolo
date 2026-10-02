"""Deprecated compatibility shim.

Canonical harmonic-turn intelligence lives in Shared Core.
"""
from music_intelligence.reasoning.harmonic_turn import (
    HarmonicTurnContext as BebopHarmonicTurnContext,
    HarmonicTurnPhase as BebopHarmonicPhase,
    derive_harmonic_turn_context as derive_bebop_harmonic_turn_context,
)
__all__=["BebopHarmonicTurnContext","BebopHarmonicPhase","derive_bebop_harmonic_turn_context"]
