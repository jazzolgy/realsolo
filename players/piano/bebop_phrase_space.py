"""Deprecated compatibility shim.

Canonical phrase-space intelligence lives in Shared Core.
"""
from music_intelligence.reasoning.phrase_space import (
    PhraseSpaceEvidence as BebopPhraseSpaceEvidence,
    PhraseSpaceType,
    classify_phrase_space,
)
__all__=["BebopPhraseSpaceEvidence","PhraseSpaceType","classify_phrase_space"]
