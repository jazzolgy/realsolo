"""Bebop bass interaction grammar v0.1.

Maps Shared Core interaction directives and local bass memory into a bass-specific
musical intention. It does not choose exact notes.

The vocabulary reflects the analytical distinction between maintaining the
harmonic/time floor and selectively answering, yielding, building, resetting, or
filling when ensemble context actually supports it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.reasoning.ensemble_state import InteractionKind
from music_intelligence.reasoning.interaction_scheduler import InteractionDirective

from .performance_memory import BassPerformanceSnapshot


class BassInteractionIntent(str, Enum):
    ANCHOR = "anchor"
    PROPEL = "propel"
    CONNECT = "connect"
    YIELD = "yield"
    ANSWER = "answer"
    FILL = "fill"
    BUILD = "build"
    RELEASE = "release"
    RESET = "reset"
    HOLD = "hold"


@dataclass(frozen=True)
class BassInteractionContext:
    directive: InteractionDirective | None = None
    memory: BassPerformanceSnapshot = BassPerformanceSnapshot()
    phrase_boundary: bool = False
    form_boundary: bool = False
    next_harmony_known: bool = False
    soloist_phrase_ending: bool = False
    drum_fill_active: bool = False
    piano_fill_active: bool = False
    low_register_conflict: bool = False
    ensemble_activity: float = 0.5


@dataclass(frozen=True)
class BassInteractionDecision:
    intent: BassInteractionIntent
    density_delta: float = 0.0
    complexity_delta: float = 0.0
    register_recovery: float = 0.0
    response_opportunity: float = 0.0
    reasons: tuple[str, ...] = ()


def choose_bass_interaction_intent(
    ctx: BassInteractionContext,
) -> BassInteractionDecision:
    """Choose a bass role intention, not an exact musical event."""
    reasons: list[str] = []
    intent = BassInteractionIntent.ANCHOR
    density = 0.0
    complexity = 0.0
    recovery = 0.0
    opportunity = 0.0

    d = ctx.directive
    if d is not None:
        if d.interaction in {InteractionKind.YIELD, InteractionKind.HOLD_SPACE}:
            intent = BassInteractionIntent.YIELD
            density -= .12
            complexity -= .16
            reasons.append("shared ensemble directive requests space")
        elif d.interaction is InteractionKind.BUILD:
            intent = BassInteractionIntent.BUILD
            density += .05
            complexity += .06
            reasons.append("shared ensemble directive supports collective build")
        elif d.interaction in {InteractionKind.LOCK, InteractionKind.SUPPORT}:
            intent = BassInteractionIntent.ANCHOR
            complexity -= .04
            reasons.append("shared ensemble directive favors bass-floor continuity")
        elif d.interaction is InteractionKind.ANSWER:
            opportunity += .35
            reasons.append("shared ensemble directive opens an answer window")
        elif d.interaction in {InteractionKind.TRANSITION, InteractionKind.SETUP}:
            intent = BassInteractionIntent.CONNECT
            reasons.append("shared transition/setup suggests directional connection")

    # Phrase ending is an opportunity, not an automatic fill.
    if ctx.soloist_phrase_ending:
        opportunity += .35
        reasons.append("soloist phrase ending creates response opportunity")

    if ctx.drum_fill_active or ctx.piano_fill_active:
        had_response_window = opportunity > 0
        opportunity -= .30
        density -= .08
        complexity -= .10
        if had_response_window or intent in {
            BassInteractionIntent.ANSWER,
            BassInteractionIntent.FILL,
        }:
            intent = BassInteractionIntent.YIELD
        reasons.append("another rhythm-section voice is already filling the space")

    if ctx.low_register_conflict:
        recovery += .18
        density -= .04
        reasons.append("low-register overlap calls for bass register/space adjustment")

    if ctx.ensemble_activity >= .78:
        density -= .10
        complexity -= .12
        opportunity -= .10
        if intent in {
            BassInteractionIntent.ANSWER,
            BassInteractionIntent.FILL,
            BassInteractionIntent.BUILD,
            BassInteractionIntent.CONNECT,
        }:
            intent = BassInteractionIntent.HOLD
        reasons.append("dense ensemble texture asks bass to simplify its information load")
    elif ctx.ensemble_activity <= .30:
        opportunity += .12
        reasons.append("open ensemble texture leaves room for bass response")

    # Local memory prevents perpetual decoration. Complexity debt is repaid by
    # anchoring/holding instead of adding another interesting gesture.
    if ctx.memory.recent_complexity >= .62:
        if intent not in {BassInteractionIntent.YIELD, BassInteractionIntent.RESET}:
            intent = BassInteractionIntent.HOLD
        complexity -= .14
        reasons.append("recent bass complexity creates a hold/simplify obligation")

    # Too much one-direction contour or a prolonged register slope asks for
    # recovery, but the exact pitch remains open.
    if (
        ctx.memory.consecutive_direction_count >= 3
        or abs(ctx.memory.phrase_register_slope) >= 2.5
    ):
        recovery += .35
        reasons.append("recent contour/register trajectory needs recovery")

    if ctx.form_boundary:
        intent = BassInteractionIntent.RESET
        complexity -= .08
        recovery = max(recovery, .45)
        reasons.append("form boundary favors orientation and register reset")
    elif ctx.phrase_boundary and intent is BassInteractionIntent.ANCHOR:
        intent = BassInteractionIntent.RELEASE
        complexity -= .04
        reasons.append("phrase boundary favors a small release before rebuilding")

    if ctx.next_harmony_known and intent in {
        BassInteractionIntent.ANCHOR,
        BassInteractionIntent.HOLD,
    }:
        # Preserve floor, but permit connective intent as harmony approaches.
        opportunity += .08

    # Only turn response opportunity into ANSWER/FILL when there is room and the
    # bass has not just been complex. This encodes "opportunity != obligation".
    if opportunity >= .55 and ctx.memory.recent_complexity < .48:
        intent = BassInteractionIntent.ANSWER
        complexity += .06
        reasons.append("response window is open and recent bass activity leaves room")

    return BassInteractionDecision(
        intent=intent,
        density_delta=max(-1.0, min(1.0, density)),
        complexity_delta=max(-1.0, min(1.0, complexity)),
        register_recovery=max(0.0, min(1.0, recovery)),
        response_opportunity=max(0.0, min(1.0, opportunity)),
        reasons=tuple(reasons),
    )
