"""Bebop bass-drums coupling adapter.

Consumes Shared EnsembleState read-only.  It never chooses bass notes or changes
Shared Core.  The purpose is to estimate how much rhythmic floor the bass is
already supplying so the drummer can choose complementary rather than
duplicative behavior.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    InteractionKind,
    PlayerActionIntent,
    PlayerRole,
)

from .bebop import BassDrumIntent, BebopInteractionState
from .model import DrumGesture, DrumVoice, GestureRole


@dataclass(frozen=True)
class BassPulseProjection:
    bass_player_id: str | None
    present: bool
    pulse_confidence: float
    walking_confidence: float
    density: float
    energy: float
    phrase_maturity: float
    lock_intent: float
    accent_request: float
    source_tags: frozenset[str] = frozenset()

    def validate(self) -> None:
        for name in (
            "pulse_confidence",
            "walking_confidence",
            "density",
            "energy",
            "phrase_maturity",
            "lock_intent",
            "accent_request",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


@dataclass(frozen=True)
class BassDrumsCoupling:
    shared_pulse: float
    drummer_freedom: float
    floor_support_need: float
    accent_alignment_opportunity: float
    low_end_overlap_risk: float
    reasons: tuple[str, ...]

    def validate(self) -> None:
        for name in (
            "shared_pulse",
            "drummer_freedom",
            "floor_support_need",
            "accent_alignment_opportunity",
            "low_end_overlap_risk",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


def _latest_intent_for(state: EnsembleState, player_id: str) -> PlayerActionIntent | None:
    return state.intent_for(player_id)


def project_bass_pulse(state: EnsembleState) -> BassPulseProjection:
    """Project shared bass intent into drummer-readable rhythmic evidence."""
    state.validate()
    bass_players = [
        p for p in state.players
        if p.active and p.role is PlayerRole.BASS
    ]
    if not bass_players:
        projection = BassPulseProjection(
            bass_player_id=None,
            present=False,
            pulse_confidence=0.0,
            walking_confidence=0.0,
            density=0.0,
            energy=0.0,
            phrase_maturity=0.0,
            lock_intent=0.0,
            accent_request=0.0,
        )
        projection.validate()
        return projection

    bass = bass_players[0]
    intent = _latest_intent_for(state, bass.player_id)
    if intent is None:
        projection = BassPulseProjection(
            bass_player_id=bass.player_id,
            present=True,
            pulse_confidence=0.35,
            walking_confidence=0.0,
            density=0.5,
            energy=0.5,
            phrase_maturity=0.0,
            lock_intent=0.0,
            accent_request=0.0,
        )
        projection.validate()
        return projection

    tags = set(intent.tags)
    quarter = 1.0 if "quarter_note_pulse" in tags else 0.0
    walking = 1.0 if "walking" in tags else 0.0
    lock = 1.0 if intent.interaction is InteractionKind.LOCK else 0.0
    accent = 1.0 if (
        "ensemble_kick" in tags
        or "figure" in tags
        or intent.interaction in {InteractionKind.PUNCTUATE, InteractionKind.SETUP}
    ) else 0.0

    pulse = min(
        1.0,
        0.18
        + 0.34 * quarter
        + 0.22 * walking
        + 0.16 * lock
        + 0.10 * intent.density,
    )
    projection = BassPulseProjection(
        bass_player_id=bass.player_id,
        present=True,
        pulse_confidence=pulse,
        walking_confidence=walking,
        density=intent.density,
        energy=intent.energy,
        phrase_maturity=intent.phrase_maturity,
        lock_intent=lock,
        accent_request=accent,
        source_tags=intent.tags,
    )
    projection.validate()
    return projection


def infer_bass_drums_coupling(
    bass: BassPulseProjection,
    *,
    interaction_state: BebopInteractionState,
) -> BassDrumsCoupling:
    """Estimate complementary rhythmic responsibilities.

    Strong walking/quarter-note bass increases shared pulse and permits greater
    drum-surface freedom.  It usually *reduces* the need for audible bass-drum
    floor duplication while leaving explicit accent alignment available.
    """
    bass.validate()
    reasons: list[str] = []

    if not bass.present:
        result = BassDrumsCoupling(
            shared_pulse=0.20,
            drummer_freedom=0.25,
            floor_support_need=0.72,
            accent_alignment_opportunity=0.10,
            low_end_overlap_risk=0.05,
            reasons=("no active bass player detected",),
        )
        result.validate()
        return result

    shared = min(
        1.0,
        0.58 * bass.pulse_confidence
        + 0.24 * bass.lock_intent
        + 0.18 * bass.walking_confidence,
    )
    freedom = min(1.0, 0.28 + 0.62 * shared)
    floor_need = max(0.0, 0.70 - 0.55 * shared)
    overlap = min(
        1.0,
        0.18
        + 0.44 * bass.density
        + 0.24 * bass.energy
        + 0.14 * bass.walking_confidence,
    )
    alignment = min(
        1.0,
        0.12
        + 0.60 * bass.accent_request
        + 0.16 * bass.phrase_maturity
        + (0.10 if interaction_state is BebopInteractionState.HANDOFF else 0.0),
    )

    if shared >= 0.65:
        reasons.append("bass provides a strong rhythmic floor")
    if bass.walking_confidence >= 0.8:
        reasons.append("walking bass supports quarter-note continuity")
    if overlap >= 0.62:
        reasons.append("avoid unnecessary low-frequency duplication")
    if alignment >= 0.6:
        reasons.append("bass intent creates an accent-alignment window")
    if interaction_state is BebopInteractionState.COAST:
        freedom = min(1.0, freedom + 0.06)
        floor_need = max(0.0, floor_need - 0.08)
        reasons.append("coast state favors ride clarity over extra kick activity")

    result = BassDrumsCoupling(
        shared_pulse=shared,
        drummer_freedom=freedom,
        floor_support_need=floor_need,
        accent_alignment_opportunity=alignment,
        low_end_overlap_risk=overlap,
        reasons=tuple(reasons),
    )
    result.validate()
    return result


def coupling_score_adjustment(
    gesture: DrumGesture,
    *,
    bass_intent: BassDrumIntent | None,
    coupling: BassDrumsCoupling,
) -> tuple[float, tuple[tuple[str, float], ...]]:
    """Return bebop bass/drums complementarity adjustment for one gesture."""
    coupling.validate()
    score = 0.0
    parts: list[tuple[str, float]] = []
    has_ride = any(h.voice is DrumVoice.RIDE for h in gesture.hits)
    has_bass_drum = any(h.voice is DrumVoice.BASS_DRUM for h in gesture.hits)

    if has_ride and coupling.shared_pulse >= 0.55:
        # Strong bass floor lets the ride remain clear while the rest of the kit
        # need not duplicate every pulse.
        v = 0.10 * coupling.drummer_freedom
        score += v
        parts.append(("bass_enables_ride_freedom", v))

    if has_bass_drum and bass_intent is BassDrumIntent.FLOOR_SUPPORT:
        v = 0.20 * coupling.floor_support_need - 0.18 * coupling.low_end_overlap_risk
        score += v
        parts.append(("bass_floor_complementarity", v))

    if has_bass_drum and bass_intent in {
        BassDrumIntent.INTERACTIVE_ACCENT,
        BassDrumIntent.ENSEMBLE_FIGURE_SUPPORT,
    }:
        v = 0.24 * coupling.accent_alignment_opportunity
        score += v
        parts.append(("selective_bass_drum_alignment", v))

    if (
        has_bass_drum
        and coupling.low_end_overlap_risk >= 0.7
        and coupling.accent_alignment_opportunity < 0.35
    ):
        v = -0.14 * coupling.low_end_overlap_risk
        score += v
        parts.append(("avoid_low_end_duplication", v))

    if gesture.role is GestureRole.SPACE and coupling.shared_pulse >= 0.7:
        v = 0.08 * coupling.shared_pulse
        score += v
        parts.append(("bass_holds_floor_for_drum_space", v))

    return score, tuple(parts)
