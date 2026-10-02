"""Bass Performance Grammar v0.1.

Instrument-specific decision semantics for immediate bass realization.

This layer deliberately does not infer harmony, chord scales, form, or generic
voice-leading. Those remain Shared Core responsibilities. It describes how a
bass player may realize already-understood musical context as one immediate
action.

Source-grounded principles used in this baseline:
- walking time centers a quarter-note pulse;
- the final beat before a harmony change is a privileged preparation/approach
  position;
- chordal, scalar and chromatic movement are distinct line-building behaviors,
  but scale membership must come from Shared Core rather than this module;
- repeated notes, register direction and groove placement are bass realization
  choices rather than harmony semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MetricRole(str, Enum):
    HARMONIC_ANCHOR = "harmonic_anchor"
    CONTINUATION = "continuation"
    PREPARATION = "preparation"
    TWO_FEEL_ANCHOR = "two_feel_anchor"
    PEDAL_ANCHOR = "pedal_anchor"


class MotionStrategy(str, Enum):
    CHORDAL = "chordal"
    SHARED_SCALE_OR_COLOR = "shared_scale_or_color"
    CHROMATIC_APPROACH = "chromatic_approach"
    DIRECT_ANTICIPATION = "direct_anticipation"
    PEDAL = "pedal"


class TargetStrategy(str, Enum):
    CURRENT_ROOT = "current_root"
    CURRENT_CHORD_MEMBER = "current_chord_member"
    NEXT_ROOT = "next_root"
    NONE = "none"


class RegisterIntent(str, Enum):
    STABLE = "stable"
    ASCEND = "ascend"
    DESCEND = "descend"


class GrooveRelation(str, Enum):
    ON_PULSE = "on_pulse"
    PREPARE_CHANGE = "prepare_change"
    SUSTAIN_ANCHOR = "sustain_anchor"


class ArticulationIntent(str, Enum):
    NEUTRAL = "neutral"
    CONNECTED = "connected"
    SHORT = "short"
    GHOSTED = "ghosted"


@dataclass(frozen=True)
class BassGrammarContext:
    beat_in_measure: float
    meter_numerator: int = 4
    walking: bool = True
    two_feel: bool = False
    pedal: bool = False
    previous_pitch_midi: int | None = None
    register_intent: RegisterIntent = RegisterIntent.STABLE
    repeated_note_tolerance: float = 0.35
    ensemble_activity: float = 0.5

    def validate(self) -> None:
        if self.meter_numerator <= 0:
            raise ValueError("meter_numerator must be positive")
        if not 0.0 <= self.beat_in_measure < self.meter_numerator:
            raise ValueError("beat_in_measure must fall inside the current measure")
        if self.previous_pitch_midi is not None and not 0 <= self.previous_pitch_midi <= 127:
            raise ValueError("previous_pitch_midi must be in MIDI range")
        if not 0.0 <= self.repeated_note_tolerance <= 1.0:
            raise ValueError("repeated_note_tolerance must be within 0..1")
        if not 0.0 <= self.ensemble_activity <= 1.0:
            raise ValueError("ensemble_activity must be within 0..1")


@dataclass(frozen=True)
class BassGrammarDecision:
    metric_role: MetricRole
    motion_strategy: MotionStrategy
    target_strategy: TargetStrategy
    groove_relation: GrooveRelation
    articulation_intent: ArticulationIntent
    score_delta: float
    reasons: tuple[str, ...] = ()


def metric_role(ctx: BassGrammarContext) -> MetricRole:
    ctx.validate()
    if ctx.pedal:
        return MetricRole.PEDAL_ANCHOR
    if ctx.two_feel:
        return MetricRole.TWO_FEEL_ANCHOR
    if ctx.walking and ctx.beat_in_measure >= ctx.meter_numerator - 1.0:
        return MetricRole.PREPARATION
    if abs(ctx.beat_in_measure) < 1e-9:
        return MetricRole.HARMONIC_ANCHOR
    return MetricRole.CONTINUATION


def evaluate_bass_grammar(
    *,
    ctx: BassGrammarContext,
    candidate_pitch_midi: int,
    motion_strategy: MotionStrategy,
    target_strategy: TargetStrategy,
) -> BassGrammarDecision:
    """Evaluate one immediate candidate using bass-specific grammar.

    This score is intentionally modest. Shared harmony/voice-leading and later
    style/legend/ensemble policies are expected to contribute independently.
    """
    ctx.validate()
    if not 0 <= candidate_pitch_midi <= 127:
        raise ValueError("candidate_pitch_midi must be in MIDI range")

    role = metric_role(ctx)
    score = 0.0
    reasons: list[str] = []

    if role is MetricRole.HARMONIC_ANCHOR:
        if target_strategy is TargetStrategy.CURRENT_ROOT:
            score += .16
            reasons.append("beat-one harmonic anchoring")
        elif motion_strategy is MotionStrategy.CHROMATIC_APPROACH:
            score -= .10
            reasons.append("avoid spending the main anchor on an unprepared chromatic approach")

    elif role is MetricRole.PREPARATION:
        if motion_strategy is MotionStrategy.CHROMATIC_APPROACH:
            score += .22
            reasons.append("last-beat preparation toward known next harmony")
        elif motion_strategy is MotionStrategy.DIRECT_ANTICIPATION:
            score += .10
            reasons.append("late-measure direct anticipation")
        elif target_strategy is TargetStrategy.CURRENT_ROOT:
            score -= .05
            reasons.append("last beat can carry directional preparation")

    elif role is MetricRole.TWO_FEEL_ANCHOR:
        if target_strategy is TargetStrategy.CURRENT_ROOT:
            score += .12
            reasons.append("two-feel root anchor")
        elif motion_strategy is MotionStrategy.CHORDAL:
            score += .04
            reasons.append("two-feel chordal support")

    elif role is MetricRole.PEDAL_ANCHOR:
        if motion_strategy is MotionStrategy.PEDAL:
            score += .18
            reasons.append("pedal sustains a stable bass anchor")

    else:
        if motion_strategy in {
            MotionStrategy.CHORDAL,
            MotionStrategy.SHARED_SCALE_OR_COLOR,
        }:
            score += .05
            reasons.append("middle-beat line continuation")

    if ctx.previous_pitch_midi is not None:
        delta = candidate_pitch_midi - ctx.previous_pitch_midi
        if delta == 0:
            penalty = .12 * (1.0 - ctx.repeated_note_tolerance)
            score -= penalty
            reasons.append("repeated-note pressure")
        elif ctx.register_intent is RegisterIntent.ASCEND:
            if delta > 0:
                score += .05
                reasons.append("supports ascending register trajectory")
            else:
                score -= .03
        elif ctx.register_intent is RegisterIntent.DESCEND:
            if delta < 0:
                score += .05
                reasons.append("supports descending register trajectory")
            else:
                score -= .03

    if ctx.ensemble_activity > .82 and motion_strategy in {
        MotionStrategy.CHROMATIC_APPROACH,
        MotionStrategy.SHARED_SCALE_OR_COLOR,
    }:
        score -= .03
        reasons.append("busy ensemble favors a simpler bass action")

    if role is MetricRole.PREPARATION:
        groove = GrooveRelation.PREPARE_CHANGE
    elif role is MetricRole.PEDAL_ANCHOR:
        groove = GrooveRelation.SUSTAIN_ANCHOR
    else:
        groove = GrooveRelation.ON_PULSE

    articulation = (
        ArticulationIntent.CONNECTED
        if motion_strategy in {
            MotionStrategy.CHROMATIC_APPROACH,
            MotionStrategy.DIRECT_ANTICIPATION,
        }
        else ArticulationIntent.NEUTRAL
    )

    return BassGrammarDecision(
        metric_role=role,
        motion_strategy=motion_strategy,
        target_strategy=target_strategy,
        groove_relation=groove,
        articulation_intent=articulation,
        score_delta=score,
        reasons=tuple(reasons),
    )
