"""Bebop-specific drummer intelligence.

This layer is instrument/style-owned. It consumes Shared Core projections but
does not redefine canonical phrase, form, ensemble, or tension semantics.

The model reflects source-supported distinctions from the uploaded Charlie
Parker compilation study and John Riley's bop method material:
- ride-led time with variable surface realization
- bass-drum floor support vs interactive accent vs ensemble figure
- selective comping and intentional non-response
- soloist-energy interaction states including BUILD / COAST / COME_DOWN
- phrase-scale pacing rather than subdivision-independent random comping
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BebopTimeIntent(str, Enum):
    HOLD_PULSE = "hold_pulse"
    LIFT_SKIP = "lift_skip"
    QUARTER_DRIVE = "quarter_drive"
    RELAX_SURFACE = "relax_surface"
    REASSERT_TIME = "reassert_time"


class BebopCompIntent(str, Enum):
    SUPPORT = "support"
    ANSWER = "answer"
    STIMULATE = "stimulate"
    PUNCTUATE = "punctuate"
    CONTRAST = "contrast"
    COAST = "coast"
    INTENTIONAL_NON_RESPONSE = "intentional_non_response"


class BassDrumIntent(str, Enum):
    FLOOR_SUPPORT = "floor_support"
    INTERACTIVE_ACCENT = "interactive_accent"
    ENSEMBLE_FIGURE_SUPPORT = "ensemble_figure_support"
    SETUP = "setup"
    SPACE = "space"


class BebopInteractionState(str, Enum):
    LISTEN = "listen"
    SUPPORT = "support"
    BUILD = "build"
    COAST = "coast"
    COME_DOWN = "come_down"
    RELEASE = "release"
    HANDOFF = "handoff"


@dataclass(frozen=True)
class BebopPhraseMemory:
    recent_comp_density: float = 0.0
    bars_since_last_statement: float = 0.0
    recent_response_count: int = 0
    recent_non_response_count: int = 0
    last_comp_phase: float | None = None

    def validate(self) -> None:
        if not 0.0 <= self.recent_comp_density <= 1.0:
            raise ValueError("recent_comp_density must be within 0..1")
        if self.bars_since_last_statement < 0:
            raise ValueError("bars_since_last_statement may not be negative")
        if self.recent_response_count < 0 or self.recent_non_response_count < 0:
            raise ValueError("response counters may not be negative")
        if self.last_comp_phase is not None and not 0.0 <= self.last_comp_phase <= 1.0:
            raise ValueError("last_comp_phase must be normalized to 0..1")


@dataclass(frozen=True)
class SoloistEnergyProjection:
    activity: float
    current_energy: float
    energy_slope: float
    phrase_terminal_probability: float = 0.0
    climax_probability: float = 0.0

    def validate(self) -> None:
        for name in ("activity", "current_energy", "phrase_terminal_probability", "climax_probability"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if not -1.0 <= self.energy_slope <= 1.0:
            raise ValueError("energy_slope must be within -1..1")


@dataclass(frozen=True)
class BebopInteractionDecision:
    state: BebopInteractionState
    confidence: float
    reasons: tuple[str, ...]


def infer_bebop_interaction_state(
    soloist: SoloistEnergyProjection,
    memory: BebopPhraseMemory,
    *,
    drummer_energy: float,
    phrase_position: float,
    section_transition: bool = False,
) -> BebopInteractionDecision:
    """Infer a musical interaction state without equating activity with density.

    This is a deterministic research baseline.  It should later be replaced or
    calibrated by expert annotations and learned preference data.
    """
    soloist.validate()
    memory.validate()
    if not 0.0 <= drummer_energy <= 1.0:
        raise ValueError("drummer_energy must be within 0..1")
    if not 0.0 <= phrase_position <= 1.0:
        raise ValueError("phrase_position must be within 0..1")

    if section_transition or phrase_position >= 0.97:
        return BebopInteractionDecision(
            BebopInteractionState.HANDOFF,
            0.9,
            ("structural boundary", "prepare clear re-entry/handoff"),
        )

    if soloist.climax_probability >= 0.72 and soloist.energy_slope < -0.05:
        return BebopInteractionDecision(
            BebopInteractionState.COME_DOWN,
            0.84,
            ("climax likely passed", "soloist energy falling"),
        )

    if soloist.energy_slope >= 0.22:
        # Rising soloist energy does not automatically mean BUILD.
        # When the drummer has already been active, coasting preserves headroom.
        if memory.recent_comp_density >= 0.55 or memory.recent_response_count >= 3:
            return BebopInteractionDecision(
                BebopInteractionState.COAST,
                0.78,
                ("soloist rising", "drummer recently active", "preserve foreground space"),
            )
        return BebopInteractionDecision(
            BebopInteractionState.BUILD,
            0.72,
            ("soloist rising", "drummer has activity headroom"),
        )

    if soloist.activity >= 0.78 and memory.recent_comp_density >= 0.45:
        return BebopInteractionDecision(
            BebopInteractionState.COAST,
            0.75,
            ("dense soloist phrase", "avoid overstimulation"),
        )

    if soloist.phrase_terminal_probability >= 0.7:
        return BebopInteractionDecision(
            BebopInteractionState.LISTEN,
            0.72,
            ("possible phrase ending", "wait for response opening"),
        )

    if soloist.activity <= 0.28 and memory.bars_since_last_statement >= 1.0:
        return BebopInteractionDecision(
            BebopInteractionState.SUPPORT,
            0.68,
            ("soloist left space", "drummer has not stated recently"),
        )

    return BebopInteractionDecision(
        BebopInteractionState.LISTEN,
        0.6,
        ("no strong escalation/de-escalation cue",),
    )


def choose_comp_intent(
    interaction: BebopInteractionDecision,
    memory: BebopPhraseMemory,
    *,
    phrase_position: float,
) -> BebopCompIntent:
    memory.validate()
    if not 0.0 <= phrase_position <= 1.0:
        raise ValueError("phrase_position must be within 0..1")

    if interaction.state is BebopInteractionState.COAST:
        return BebopCompIntent.INTENTIONAL_NON_RESPONSE
    if interaction.state is BebopInteractionState.BUILD:
        return BebopCompIntent.STIMULATE
    if interaction.state is BebopInteractionState.COME_DOWN:
        return BebopCompIntent.SUPPORT
    if interaction.state is BebopInteractionState.HANDOFF:
        return BebopCompIntent.PUNCTUATE
    if interaction.state is BebopInteractionState.LISTEN:
        if memory.recent_response_count > memory.recent_non_response_count:
            return BebopCompIntent.INTENTIONAL_NON_RESPONSE
        if phrase_position >= 0.8:
            return BebopCompIntent.ANSWER
        return BebopCompIntent.SUPPORT
    return BebopCompIntent.SUPPORT
