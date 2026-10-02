"""Shared reasoning layer for RealSolo."""

from .harmonic_player_bridge import (
    HarmonicCandidateGuidance,
    apply_harmonic_guidance_to_monophonic_score,
    apply_harmonic_guidance_to_polyphonic_score,
    harmonic_guidance_for_candidate,
    rerank_monophonic_with_harmony,
    rerank_polyphonic_with_harmony,
)

__all__ = [
    "HarmonicCandidateGuidance",
    "apply_harmonic_guidance_to_monophonic_score",
    "apply_harmonic_guidance_to_polyphonic_score",
    "harmonic_guidance_for_candidate",
    "rerank_monophonic_with_harmony",
    "rerank_polyphonic_with_harmony",
    "CommitmentState",
    "EnsembleState",
    "InteractionEvent",
    "InteractionKind",
    "PlayerActionIntent",
    "PlayerEnsembleView",
    "PlayerPresence",
    "PlayerRole",
    "TransportState",
    "advance_transport",
    "append_interaction",
    "player_view",
    "update_player_intent",
]

from .ensemble_state import (
    CommitmentState,
    EnsembleState,
    InteractionEvent,
    InteractionKind,
    PlayerActionIntent,
    PlayerEnsembleView,
    PlayerPresence,
    PlayerRole,
    TransportState,
    advance_transport,
    append_interaction,
    player_view,
    update_player_intent,
)
