"""Deprecated compatibility shim.

Canonical solo phrase intention lives in Shared Core.
"""
from music_intelligence.reasoning.solo_phrase_intent import (
    SoloDensityDirection as BebopDensityDirection,
    SoloEntryMode as BebopEntryMode,
    SoloPhraseIntent as BebopPhraseIntent,
    SoloTargetMode as BebopTargetMode,
    derive_solo_phrase_intent as derive_bebop_phrase_intent,
)
__all__=["BebopDensityDirection","BebopEntryMode","BebopPhraseIntent","BebopTargetMode","derive_bebop_phrase_intent"]
