"""Shared prediction of intro-to-ensemble entry readiness."""
from __future__ import annotations

from .representation import EntryAction, EntryDecision, IntroMode, IntroObservation, IntroState, clamp01, with_generation


def _top_mode(state: IntroState) -> IntroMode:
    if not state.mode_hypotheses:
        return IntroMode.UNKNOWN
    return max(state.mode_hypotheses, key=lambda h: h.confidence).mode


def update_entry_readiness(
    state: IntroState,
    observation: IntroObservation,
) -> IntroState:
    state.validate()
    observation.validate()

    harmonic = max(
        observation.harmonic_arrival_confidence,
        observation.expected_head_harmony_match,
    )
    temporal = 0.45 * state.pulse_confidence + 0.35 * state.beat_phase_confidence + 0.20 * state.tempo_stability
    phrase = observation.phrase_boundary_confidence
    pickup = max(state.pickup_probability, observation.pickup_confidence)

    readiness = clamp01(
        0.32 * temporal
        + 0.28 * harmonic
        + 0.22 * phrase
        + 0.18 * pickup
    )

    # Direct head and stable vocal count-ins can legitimately become ready
    # with less harmonic evidence.
    mode = _top_mode(state)
    if mode is IntroMode.DIRECT_HEAD:
        readiness = max(readiness, clamp01(0.55 * temporal + 0.45 * observation.direct_head_confidence))
    elif mode is IntroMode.VOCAL_COUNT_IN:
        readiness = max(readiness, clamp01(0.65 * temporal + 0.35 * observation.vocal_count_confidence))

    # Free rubato should not become "ready" just because harmony arrived.
    readiness = clamp01(readiness - 0.25 * state.rubato_probability * (1.0 - state.pulse_confidence))

    target = observation.beat_phase_hint
    if target is None and pickup >= 0.6:
        target = 0.0

    join_confidence = clamp01(
        0.46 * readiness
        + 0.42 * state.entry_permission
        + 0.12 * (1.0 - state.ambiguity)
    )

    return with_generation(
        state,
        observed_harmony_id=observation.observed_harmony_id or state.observed_harmony_id,
        expected_head_harmony_id=observation.expected_head_harmony_id or state.expected_head_harmony_id,
        entry_readiness=readiness,
        entry_target_beat_phase=target,
        join_confidence=join_confidence,
        ensemble_energy=observation.ensemble_energy,
        dynamic_intent=observation.dynamic_intent,
        last_timestamp=observation.timestamp,
        provenance=state.provenance + ("entry_readiness_update",),
    )


def make_entry_decision(state: IntroState) -> EntryDecision:
    state.validate()
    rationale = [
        f"readiness:{state.entry_readiness:.3f}",
        f"permission:{state.entry_permission:.3f}",
        f"join:{state.join_confidence:.3f}",
    ]
    if state.rubato_probability > 0.55:
        rationale.append("rubato_caution")
    if state.ambiguity > 0.7:
        rationale.append("mode_ambiguous")
    return EntryDecision(
        action=EntryAction.WAIT,  # policy assigns the final action
        readiness=state.entry_readiness,
        permission=state.entry_permission,
        confidence=state.join_confidence,
        target_beat_phase=state.entry_target_beat_phase,
        rationale=tuple(rationale),
    )
