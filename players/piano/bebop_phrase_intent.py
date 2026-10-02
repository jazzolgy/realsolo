"""Soft bebop phrase intention for Parker-prior piano soloing.

The intention spans a short horizon but never freezes exact future notes.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.reasoning.online_improviser import SoftPlan
from music_intelligence.reasoning.solo_grammar import (
    SoloArc,
    SoloDevelopmentOperation,
    SoloMethodContext,
    shared_solo_method_options,
)

from .bebop_complementarity import EnsembleBreathType, EnsembleComplementarityEvidence
from .bebop_harmonic_turn import BebopHarmonicPhase, BebopHarmonicTurnContext
from .bebop_turn_taking import BebopTurnTakingEvidence, BebopTurnTakingType


class BebopEntryMode(str, Enum):
    CONTINUE = "continue"
    PICKUP = "pickup"
    NEW_PHRASE = "new_phrase"
    HOLD_SPACE = "hold_space"


class BebopTargetMode(str, Enum):
    GUIDE_TONE = "guide_tone"
    NEXT_HARMONY = "next_harmony"
    RESOLUTION = "resolution"
    COLOR = "color"
    OPEN = "open"


class BebopDensityDirection(str, Enum):
    SPARSE = "sparse"
    STABLE = "stable"
    BUILD = "build"
    RELEASE = "release"


@dataclass(frozen=True)
class BebopPhraseIntent:
    horizon_beats: float
    entry_mode: BebopEntryMode
    target_mode: BebopTargetMode
    density_direction: BebopDensityDirection
    connector_families: tuple[str, ...]
    solo_method: SoloDevelopmentOperation = SoloDevelopmentOperation.STATE
    register_direction: str = "stable"
    confidence: float = 0.5
    rationale: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.horizon_beats <= 0:
            raise ValueError("horizon_beats must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")

    def to_soft_plan(self) -> SoftPlan:
        self.validate()
        return SoftPlan(
            horizon_beats=self.horizon_beats,
            intention=f"{self.entry_mode.value}:{self.target_mode.value}",
            soft_targets=(self.target_mode.value,),
            candidate_families=self.connector_families + (f"solo_method:{self.solo_method.value}",),
            register_direction=self.register_direction,
            density_direction=self.density_direction.value,
            exact_future_notes=(),
        )


def derive_bebop_phrase_intent(
    harmonic_turn: BebopHarmonicTurnContext,
    turn: BebopTurnTakingEvidence,
    complementarity: EnsembleComplementarityEvidence,
) -> BebopPhraseIntent:
    """Derive a short intention from current harmonic and ensemble context."""
    harmonic_turn.validate()
    turn.validate()
    complementarity.validate()

    reasons: list[str]=[]
    entry=BebopEntryMode.CONTINUE
    target=BebopTargetMode.GUIDE_TONE
    density=BebopDensityDirection.STABLE
    families=("passing","neighbor","close_approach")
    horizon=2.0
    register="stable"

    if harmonic_turn.phase is BebopHarmonicPhase.ANTICIPATORY:
        entry=BebopEntryMode.PICKUP
        target=BebopTargetMode.NEXT_HARMONY
        families=("anticipation","close_approach","passing")
        horizon=1.5
        reasons.append("future harmony is known")

    elif harmonic_turn.phase is BebopHarmonicPhase.DIRECTED_RESOLUTION:
        target=BebopTargetMode.RESOLUTION
        families=("directed_target","resolution_path","close_approach")
        density=BebopDensityDirection.STABLE
        horizon=2.0
        reasons.append("current harmony carries resolution pressure")

    elif harmonic_turn.phase is BebopHarmonicPhase.STABLE_FIELD:
        target=BebopTargetMode.COLOR
        families=("passing","neighbor","motif_continuation","color_tone")
        horizon=3.0
        reasons.append("stable field permits connective development")

    elif harmonic_turn.phase is BebopHarmonicPhase.FORM_BOUNDARY:
        entry=BebopEntryMode.NEW_PHRASE
        target=BebopTargetMode.OPEN
        density=BebopDensityDirection.RELEASE
        families=("phrase_entry","pickup","guide_tone")
        horizon=1.5
        reasons.append("form boundary permits phrase reset")

    if turn.episode_type is BebopTurnTakingType.SUPPORTED_HANDOFF_REENTRY:
        entry=BebopEntryMode.CONTINUE
        reasons.append("foreground has already re-entered after supported handoff")

    elif turn.episode_type is BebopTurnTakingType.COLLECTIVE_RELEASE_REENTRY:
        if harmonic_turn.phase is BebopHarmonicPhase.FORM_BOUNDARY:
            entry=BebopEntryMode.NEW_PHRASE
        else:
            entry=BebopEntryMode.CONTINUE
        reasons.append("collective release has already resolved into re-entry")

    elif turn.episode_type is BebopTurnTakingType.FOREGROUND_CONTINUES:
        density=BebopDensityDirection.SPARSE
        reasons.append("continued foreground activity favors contrast")

    if complementarity.breath_type is EnsembleBreathType.FOREGROUND_HANDOFF:
        if max(
            complementarity.low_harmonic_support,
            complementarity.percussive_support,
        ) >= 0.8:
            density=BebopDensityDirection.SPARSE
            reasons.append("active support already carries the handoff")

    elif complementarity.breath_type is EnsembleBreathType.COLLECTIVE_RELEASE:
        if turn.episode_type is not BebopTurnTakingType.COLLECTIVE_RELEASE_REENTRY:
            entry=BebopEntryMode.HOLD_SPACE
            density=BebopDensityDirection.RELEASE
            target=BebopTargetMode.OPEN
            families=("rest","pickup","phrase_entry")
            reasons.append("collective release has not yet clearly re-entered")

    shared_context = SoloMethodContext(
        phrase_maturity=max(0.0, min(1.0, 1.0 - harmonic_turn.phrase_boundary_pressure)),
        tension=max(0.0, min(1.0, harmonic_turn.resolution_strength)),
        ensemble_activity=max(
            0.0,
            min(
                1.0,
                max(
                    complementarity.low_harmonic_support,
                    complementarity.percussive_support,
                ),
            ),
        ),
        recent_repetition_count=0,
        phrase_space_available=max(0.0, min(1.0, complementarity.foreground_drop)),
        form_boundary_pressure=max(0.0, min(1.0, harmonic_turn.phrase_boundary_pressure)),
        future_harmony_available=harmonic_turn.phase is BebopHarmonicPhase.ANTICIPATORY,
        interaction_role=(
            "ANSWER"
            if turn.episode_type is BebopTurnTakingType.SUPPORTED_HANDOFF_REENTRY
            else ""
        ),
    )
    shared_arc = (
        SoloArc.RELEASE
        if density is BebopDensityDirection.RELEASE
        else SoloArc.DEVELOP
    )
    shared_options = shared_solo_method_options(shared_context, arc=shared_arc)
    solo_method = max(shared_options, key=lambda option: option.weight).operation
    reasons.append(f"shared solo method: {solo_method.value}")

    confidence=max(
        0.25,
        min(
            1.0,
            0.45*harmonic_turn.confidence
            + 0.30*turn.confidence
            + 0.25*complementarity.confidence,
        ),
    )

    intent=BebopPhraseIntent(
        horizon_beats=horizon,
        entry_mode=entry,
        target_mode=target,
        density_direction=density,
        connector_families=families,
        solo_method=solo_method,
        register_direction=register,
        confidence=confidence,
        rationale=tuple(reasons),
    )
    intent.validate()
    return intent
