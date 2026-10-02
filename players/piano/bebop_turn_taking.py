"""Deprecated compatibility shim.

Canonical turn-taking intelligence lives in
music_intelligence.reasoning.turn_taking.
"""
from music_intelligence.reasoning.turn_taking import (
    TurnTakingEvidence as BebopTurnTakingEvidence,
    TurnTakingType as BebopTurnTakingType,
    classify_turn_taking as classify_bebop_turn_taking,
)
__all__=["BebopTurnTakingEvidence","BebopTurnTakingType","classify_bebop_turn_taking"]
