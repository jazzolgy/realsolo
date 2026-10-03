"""Bridge live ensemble evidence into Shared Solo Intelligence.

This module is intentionally instrument-neutral. It turns the previous
published EnsembleState plus current harmony into the Shared Solo inputs used by
Players. It never chooses a sax fingering, piano voicing, bass string, or drum
hit.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.harmony.jazz_harmony_core import HarmonicFrame
from music_intelligence.reasoning.ensemble_complementarity import (
    EnsembleComplementarityEvidence,
    classify_ensemble_complementarity,
)
from music_intelligence.reasoning.ensemble_state import EnsembleState
from music_intelligence.reasoning.harmonic_turn import (
    HarmonicTurnContext,
    derive_harmonic_turn_context,
)
from music_intelligence.reasoning.turn_taking import (
    TurnTakingEvidence,
    classify_turn_taking,
)


@dataclass(frozen=True)
class SharedSoloMoment:
    turn: TurnTakingEvidence
    complementarity: EnsembleComplementarityEvidence
    harmonic_turn: HarmonicTurnContext


def _intent_density(state: EnsembleState, player_id: str, default: float) -> float:
    intent=state.intent_for(player_id)
    return default if intent is None else max(0.0,min(1.0,intent.density))


def derive_shared_solo_moment(
    state: EnsembleState,
    frame: HarmonicFrame,
    *,
    foreground_player_id: str,
) -> SharedSoloMoment:
    """Derive conservative one-tick Shared Solo evidence from prior publication.

    The current player never sees same-tick decisions. Values here summarize
    only the already-published snapshot.
    """

    foreground=_intent_density(state,foreground_player_id,.45)
    bass=_intent_density(state,"bass",.55)
    drums=_intent_density(state,"drums",.50)
    piano=_intent_density(state,"piano",.42)

    low_support=max(0.0,min(1.0,.65*bass+.35*piano))
    attack_support=max(0.0,min(1.0,drums))
    post_foreground=max(0.0,min(1.0,foreground))

    turn=classify_turn_taking(
        foreground_during_pre=foreground,
        low_support_during_pre=low_support,
        attack_support_during_pre=attack_support,
        foreground_post_during=1.0+2.0*post_foreground,
        confidence=.68,
    )
    complementarity=classify_ensemble_complementarity(
        foreground_ratio=foreground,
        low_harmonic_support_ratio=low_support,
        percussive_support_ratio=attack_support,
        post_foreground_ratio=1.0+2.0*post_foreground,
        confidence=.68,
    )
    harmonic_turn=derive_harmonic_turn_context(frame,turn)
    return SharedSoloMoment(turn,complementarity,harmonic_turn)
