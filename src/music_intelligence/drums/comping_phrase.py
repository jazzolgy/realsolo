"""Phrase-level bebop snare comping development.

This module models local drummer execution memory only. Shared Core remains the
owner of canonical motif/phrase memory.

The design is source-grounded in the uploaded John Riley bop method:
- comping ideas are paced across phrases rather than fired continuously;
- recognizable rhythmic material can return after space;
- rhythmic transposition/displacement can preserve identity at a new location;
- accompaniment is conversational and should avoid overstimulation.

No future snare sequence is frozen here.  The engine only evaluates the current
decision instant.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .bebop import BebopCompIntent, BebopInteractionState
from .model import (
    DrumGesture,
    DrumHit,
    DrummerRuntimeContext,
    DrummerSoftPlan,
    DrumVoice,
    GestureRole,
    Limb,
)
from .timing import bounded_timing_offset_ms, tempo_conditioned_swing_prior


class CompPhraseAction(str, Enum):
    STATE = "state"
    REPEAT = "repeat"
    RETURN = "return"
    DISPLACED_RETURN = "displaced_return"
    VARIATION = "variation"
    PUNCTUATE = "punctuate"
    LEAVE_SPACE = "leave_space"


@dataclass(frozen=True)
class SnareMotifIdentity:
    """Compact identity of a recently played snare idea.

    onset_phases are normalized within a bar.  They describe rhythmic identity,
    not a future score.
    """
    onset_phases: tuple[float, ...]
    accent_phases: tuple[float, ...] = ()
    density: float = 0.25
    source: str = "local_execution"

    def validate(self) -> None:
        if not self.onset_phases:
            raise ValueError("motif must contain at least one onset")
        for x in self.onset_phases + self.accent_phases:
            if not 0.0 <= x <= 1.0:
                raise ValueError("motif phases must be normalized to 0..1")
        if not 0.0 <= self.density <= 1.0:
            raise ValueError("motif density must be within 0..1")


@dataclass(frozen=True)
class SnarePhraseMemory:
    motif: SnareMotifIdentity | None = None
    bars_since_motif_statement: float = 999.0
    consecutive_related_statements: int = 0
    bars_since_any_snare_statement: float = 999.0
    last_statement_phase: float | None = None
    recent_space_bars: float = 0.0

    def validate(self) -> None:
        if self.motif is not None:
            self.motif.validate()
        for name in (
            "bars_since_motif_statement",
            "bars_since_any_snare_statement",
            "recent_space_bars",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} may not be negative")
        if self.consecutive_related_statements < 0:
            raise ValueError("consecutive_related_statements may not be negative")
        if self.last_statement_phase is not None and not 0.0 <= self.last_statement_phase <= 1.0:
            raise ValueError("last_statement_phase must be normalized to 0..1")


@dataclass(frozen=True)
class CompPhraseCandidate:
    gesture: DrumGesture
    action: CompPhraseAction
    score_bias: float
    relation_to_motif: float
    reasons: tuple[str, ...]


def normalized_bar_phase(context: DrummerRuntimeContext) -> float:
    return context.position_in_bar_beats / context.beats_per_bar


def circular_phase_distance(a: float, b: float) -> float:
    diff = abs(a - b)
    return min(diff, 1.0 - diff)


def motif_match_at_phase(
    motif: SnareMotifIdentity,
    phase: float,
    *,
    tolerance: float = 0.055,
) -> float:
    motif.validate()
    if not 0.0 <= phase <= 1.0:
        raise ValueError("phase must be normalized to 0..1")
    nearest = min(circular_phase_distance(phase, x) for x in motif.onset_phases)
    if nearest > tolerance:
        return 0.0
    return max(0.0, 1.0 - nearest / tolerance)


def displaced_motif_match(
    motif: SnareMotifIdentity,
    phase: float,
    *,
    displacement: float = 0.125,
    tolerance: float = 0.055,
) -> float:
    motif.validate()
    shifted = SnareMotifIdentity(
        onset_phases=tuple((x + displacement) % 1.0 for x in motif.onset_phases),
        accent_phases=tuple((x + displacement) % 1.0 for x in motif.accent_phases),
        density=motif.density,
        source=motif.source,
    )
    return motif_match_at_phase(shifted, phase, tolerance=tolerance)


def _snare_gesture(
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
    action: CompPhraseAction,
    *,
    velocity_delta: int = 0,
) -> DrumGesture:
    prior = tempo_conditioned_swing_prior(context.tempo_bpm)
    velocity = int(45 + 34 * plan.energy) + velocity_delta
    gesture = DrumGesture(
        hits=(
            DrumHit(
                DrumVoice.SNARE,
                Limb.LEFT_HAND,
                max(1, min(127, velocity)),
                microtiming_ms=bounded_timing_offset_ms(
                    plan.microtiming_bias_ms,
                    prior.snare_relative_ms,
                    plan.expressive_timing_offset_ms,
                    prior,
                ),
                articulation=f"comp_{action.value}",
            ),
        ),
        role=GestureRole.COMP,
        tags=frozenset({"bebop", "snare_phrase", action.value}),
        provenance=("drum_player", "snare_phrase_engine"),
    )
    gesture.validate()
    return gesture


def build_snare_phrase_candidates(
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
    interaction: BebopInteractionState,
    comp_intent: BebopCompIntent,
    memory: SnarePhraseMemory,
) -> tuple[CompPhraseCandidate, ...]:
    """Build only current-instant snare/space phrase-development candidates."""
    plan.validate()
    context.validate()
    memory.validate()
    phase = normalized_bar_phase(context)

    out: list[CompPhraseCandidate] = []

    # Silence is always a deliberate phrase-level alternative.
    space_bias = 0.10 + 0.10 * min(1.0, memory.consecutive_related_statements / 2.0)
    if interaction in {
        BebopInteractionState.COAST,
        BebopInteractionState.LISTEN,
        BebopInteractionState.COME_DOWN,
    }:
        space_bias += 0.26
    if comp_intent is BebopCompIntent.INTENTIONAL_NON_RESPONSE:
        space_bias += 0.34
    space_tags = {"bebop", "snare_phrase", "leave_space"}
    if comp_intent is BebopCompIntent.INTENTIONAL_NON_RESPONSE:
        space_tags.add("intentional_non_response")
    out.append(CompPhraseCandidate(
        DrumGesture(
            role=GestureRole.SPACE,
            tags=frozenset(space_tags),
            provenance=("drum_player", "snare_phrase_engine"),
        ),
        CompPhraseAction.LEAVE_SPACE,
        space_bias,
        0.0,
        ("phrase pacing keeps silence as an intentional action",),
    ))

    if memory.motif is None:
        # A first statement is most useful when the interaction state permits
        # foreground commentary.
        bias = 0.16
        if interaction in {BebopInteractionState.SUPPORT, BebopInteractionState.BUILD}:
            bias += 0.20
        if comp_intent in {BebopCompIntent.ANSWER, BebopCompIntent.STIMULATE}:
            bias += 0.16
        out.append(CompPhraseCandidate(
            _snare_gesture(plan, context, CompPhraseAction.STATE),
            CompPhraseAction.STATE,
            bias,
            0.0,
            ("no local snare motif exists; this can establish one",),
        ))
        return tuple(out)

    exact = motif_match_at_phase(memory.motif, phase)
    displaced = displaced_motif_match(memory.motif, phase)

    if exact > 0:
        repeat_bias = 0.10 + 0.30 * exact
        # Immediate/parroting repetition becomes less attractive.
        if memory.bars_since_motif_statement < 0.75:
            repeat_bias -= 0.26
        if memory.consecutive_related_statements >= 2:
            repeat_bias -= 0.22
        out.append(CompPhraseCandidate(
            _snare_gesture(plan, context, CompPhraseAction.REPEAT),
            CompPhraseAction.REPEAT,
            repeat_bias,
            exact,
            ("current phase recalls the stored motif",),
        ))

        if memory.bars_since_motif_statement >= 1.0:
            return_bias = 0.24 + 0.28 * exact + 0.10 * min(memory.recent_space_bars, 2.0)
            out.append(CompPhraseCandidate(
                _snare_gesture(plan, context, CompPhraseAction.RETURN, velocity_delta=3),
                CompPhraseAction.RETURN,
                return_bias,
                exact,
                ("motif returns after phrase-scale space",),
            ))

    if displaced > 0:
        disp_bias = 0.20 + 0.30 * displaced
        if memory.bars_since_motif_statement >= 0.75:
            disp_bias += 0.12
        if interaction in {BebopInteractionState.BUILD, BebopInteractionState.SUPPORT}:
            disp_bias += 0.08
        out.append(CompPhraseCandidate(
            _snare_gesture(plan, context, CompPhraseAction.DISPLACED_RETURN, velocity_delta=2),
            CompPhraseAction.DISPLACED_RETURN,
            disp_bias,
            displaced,
            ("same rhythmic identity is available at a transposed bar position",),
        ))

    # Variation is available near, but not exactly on, a known motif phase.
    nearest = max(exact, displaced)
    if nearest > 0.25 or context.phrase_position >= 0.78:
        var_bias = 0.18 + 0.20 * nearest
        if comp_intent in {BebopCompIntent.ANSWER, BebopCompIntent.CONTRAST}:
            var_bias += 0.12
        out.append(CompPhraseCandidate(
            _snare_gesture(plan, context, CompPhraseAction.VARIATION, velocity_delta=-2),
            CompPhraseAction.VARIATION,
            var_bias,
            nearest * 0.75,
            ("preserve partial identity while changing placement/weight",),
        ))

    if (
        context.phrase_position >= 0.88
        or interaction is BebopInteractionState.HANDOFF
        or comp_intent is BebopCompIntent.PUNCTUATE
    ):
        out.append(CompPhraseCandidate(
            _snare_gesture(plan, context, CompPhraseAction.PUNCTUATE, velocity_delta=10),
            CompPhraseAction.PUNCTUATE,
            0.38,
            0.0,
            ("phrase/form boundary creates a punctuation opportunity",),
        ))

    return tuple(out)


def update_snare_phrase_memory(
    memory: SnarePhraseMemory,
    action: CompPhraseAction,
    *,
    phase: float,
    bar_advance: float = 0.0,
) -> SnarePhraseMemory:
    """Update local history after an immediate action.

    For a first statement, a one-onset motif identity is created from the
    committed phase. Later real implementations can aggregate multi-onset cells
    from several immediate events without ever precommitting future hits.
    """
    memory.validate()
    if not 0.0 <= phase <= 1.0:
        raise ValueError("phase must be normalized to 0..1")
    if bar_advance < 0:
        raise ValueError("bar_advance may not be negative")

    motif = memory.motif
    bars_motif = memory.bars_since_motif_statement + bar_advance
    bars_any = memory.bars_since_any_snare_statement + bar_advance
    related = memory.consecutive_related_statements
    recent_space = memory.recent_space_bars + bar_advance
    last_phase = memory.last_statement_phase

    if action is CompPhraseAction.LEAVE_SPACE:
        return SnarePhraseMemory(
            motif=motif,
            bars_since_motif_statement=bars_motif,
            consecutive_related_statements=max(0, related - (1 if bar_advance >= 1.0 else 0)),
            bars_since_any_snare_statement=bars_any,
            last_statement_phase=last_phase,
            recent_space_bars=recent_space,
        )

    if action is CompPhraseAction.STATE:
        motif = SnareMotifIdentity((phase,), density=0.25)
        related = 1
    elif action in {
        CompPhraseAction.REPEAT,
        CompPhraseAction.RETURN,
        CompPhraseAction.DISPLACED_RETURN,
        CompPhraseAction.VARIATION,
    }:
        related += 1
    else:
        related = 0

    return SnarePhraseMemory(
        motif=motif,
        bars_since_motif_statement=0.0,
        consecutive_related_statements=related,
        bars_since_any_snare_statement=0.0,
        last_statement_phase=phase,
        recent_space_bars=0.0,
    )
