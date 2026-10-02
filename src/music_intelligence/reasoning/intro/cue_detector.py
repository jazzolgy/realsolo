"""Entry-permission inference from leader and phrase cues."""
from __future__ import annotations

from .representation import IntroObservation, IntroState, clamp01, with_generation


def update_entry_permission(
    state: IntroState,
    observation: IntroObservation,
) -> IntroState:
    """Estimate whether the leader is actually inviting ensemble entry.

    Readiness and permission are intentionally separate. A dominant arrival can
    make entry structurally plausible while the leader still intends to continue
    a rubato phrase alone.
    """

    state.validate()
    observation.validate()

    cue = max(
        observation.explicit_entry_cue_confidence,
        0.85 * observation.pickup_confidence,
        0.70
        * min(
            observation.phrase_boundary_confidence,
            max(observation.expected_head_harmony_match, observation.harmonic_arrival_confidence),
        ),
    )
    hold_penalty = 0.65 * observation.leader_hold_confidence
    permission = clamp01(
        0.65 * state.entry_permission + 0.35 * cue - hold_penalty
    )

    leader = state.leader_player_id or observation.source_player_id
    return with_generation(
        state,
        leader_player_id=leader,
        entry_permission=permission,
        provenance=state.provenance + ("entry_permission_update",),
    )
