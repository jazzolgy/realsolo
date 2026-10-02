"""Online AI Drummer vertical slice.

The policy chooses exactly one immediate gesture, then the caller must listen
and call again.  Swing placement is tempo-conditioned at the current clock
position; no future bar is rendered or cached here.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .comping import comping_propensity
from .model import (
    DrumGesture,
    DrumHit,
    DrummerRuntimeContext,
    DrummerSoftPlan,
    DrumVoice,
    GestureRole,
    Limb,
    TimeFeel,
)
from .pattern_runtime import source_pattern_candidates
from .timing import (
    bounded_timing_offset_ms,
    is_ride_anchor,
    tempo_conditioned_swing_prior,
)


@dataclass(frozen=True)
class ScoredDrumGesture:
    gesture: DrumGesture
    score: float
    components: tuple[tuple[str, float], ...] = ()


@dataclass
class DrummerPerformanceMemory:
    committed: list[DrumGesture] = field(default_factory=list)

    def commit(self, gesture: DrumGesture) -> None:
        gesture.validate()
        self.committed.append(gesture)


def _base_time_hits(
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
) -> tuple[DrumHit, ...]:
    if plan.feel is not TimeFeel.SWING:
        return ()

    prior = tempo_conditioned_swing_prior(context.tempo_bpm)
    hits: list[DrumHit] = []

    # Online realization: evaluate only whether *this instant* is a ride anchor.
    if is_ride_anchor(context.position_in_bar_beats, prior):
        hits.append(DrumHit(
            DrumVoice.RIDE,
            Limb.RIGHT_HAND,
            velocity=plan.ride_velocity,
            microtiming_ms=bounded_timing_offset_ms(
                plan.microtiming_bias_ms,
                prior.ride_bias_ms,
                plan.expressive_timing_offset_ms,
                prior,
            ),
            articulation="tip",
        ))

    beat = int(context.position_in_bar_beats) + 1
    on_downbeat = abs(context.position_in_bar_beats - int(context.position_in_bar_beats)) < 1e-6
    if on_downbeat and beat in {2, 4}:
        hits.append(DrumHit(
            DrumVoice.CLOSED_HIHAT,
            Limb.LEFT_FOOT,
            velocity=max(35, plan.ride_velocity - 18),
            microtiming_ms=bounded_timing_offset_ms(
                plan.microtiming_bias_ms,
                prior.pedal_hihat_relative_ms,
                plan.expressive_timing_offset_ms,
                prior,
            ),
            articulation="chick",
        ))
    return tuple(hits)


def build_immediate_candidates(
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
) -> tuple[DrumGesture, ...]:
    """Generate only gestures playable at the current decision instant."""
    plan.validate()
    context.validate()
    base_hits = _base_time_hits(plan, context)
    prop = comping_propensity(plan, context)
    prior = tempo_conditioned_swing_prior(context.tempo_bpm)
    out: list[DrumGesture] = []

    if base_hits:
        out.append(DrumGesture(
            hits=base_hits,
            role=GestureRole.TIME,
            tags=frozenset({"timekeeping", plan.feel.value}),
        ))
    else:
        out.append(DrumGesture(role=GestureRole.SPACE, tags=frozenset({"time_space"})))

    # Stored pedagogical/transcribed patterns are a real candidate source.
    # Only their current slice is exposed; the rest of the pattern is not
    # committed, preserving listen -> re-plan semantics.
    out.extend(source_pattern_candidates(plan, context))

    # Snare and bass drum are independent candidate families.  Neither implies
    # the other, and neither is generated as a pre-written comping pattern.
    used = {h.limb for h in base_hits}
    if Limb.LEFT_HAND not in used and prop.snare > 0.12:
        out.append(DrumGesture(
            hits=base_hits + (
                DrumHit(
                    DrumVoice.SNARE,
                    Limb.LEFT_HAND,
                    velocity=int(44 + 32 * plan.energy),
                    microtiming_ms=bounded_timing_offset_ms(
                        plan.microtiming_bias_ms,
                        prior.snare_relative_ms,
                        plan.expressive_timing_offset_ms,
                        prior,
                    ),
                    articulation="comp",
                ),
            ),
            role=GestureRole.COMP,
            tags=frozenset({"timekeeping", "snare_comp"}),
        ))
    if Limb.RIGHT_FOOT not in used and prop.bass_drum > 0.12:
        out.append(DrumGesture(
            hits=base_hits + (
                DrumHit(
                    DrumVoice.BASS_DRUM,
                    Limb.RIGHT_FOOT,
                    velocity=int(40 + 34 * plan.energy),
                    microtiming_ms=bounded_timing_offset_ms(
                        plan.microtiming_bias_ms,
                        0.0,
                        plan.expressive_timing_offset_ms,
                        prior,
                    ),
                    articulation="feather_or_comp",
                ),
            ),
            role=GestureRole.COMP,
            tags=frozenset({"timekeeping", "bass_drum_comp"}),
        ))

    if context.requested_kick and Limb.RIGHT_FOOT not in used:
        out.append(DrumGesture(
            hits=base_hits + (
                DrumHit(DrumVoice.BASS_DRUM, Limb.RIGHT_FOOT, 96, plan.microtiming_bias_ms, "kick"),
            ),
            role=GestureRole.ACCENT,
            tags=frozenset({"ensemble_kick", "explicit_cue"}),
        ))

    near_boundary = context.phrase_position >= 0.82 or context.section_transition
    if near_boundary and Limb.LEFT_HAND not in used:
        out.append(DrumGesture(
            hits=base_hits + (
                DrumHit(
                    DrumVoice.SNARE,
                    Limb.LEFT_HAND,
                    velocity=int(58 + 38 * plan.energy),
                    microtiming_ms=plan.microtiming_bias_ms,
                    articulation="setup",
                ),
            ),
            role=GestureRole.SETUP,
            tags=frozenset({"phrase_punctuation", "setup"}),
        ))

    for gesture in out:
        gesture.validate()
    return tuple(out)


def score_gesture(
    gesture: DrumGesture,
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
) -> ScoredDrumGesture:
    score = 0.0
    comp: list[tuple[str, float]] = []
    prop = comping_propensity(plan, context)

    if gesture.role is GestureRole.TIME:
        v = 0.48 + 0.18 * (1.0 - abs(plan.energy - context.energy_target))
        score += v
        comp.append(("time_stability", v))

    if gesture.role is GestureRole.SPACE:
        v = 0.10 + 0.55 * prop.space
        score += v
        comp.append(("ensemble_space", v))

    if gesture.role is GestureRole.COMP:
        tags = gesture.tags
        if "snare_comp" in tags:
            v = 0.12 + 0.42 * prop.snare
            score += v
            comp.append(("snare_comping_prior", v))
        if "bass_drum_comp" in tags:
            v = 0.10 + 0.38 * prop.bass_drum
            score += v
            comp.append(("bass_drum_comping_prior", v))

        # Leave more room when the rest of the ensemble is already dense.
        v = 0.16 * (1.0 - context.ensemble_activity)
        score += v
        comp.append(("activity_headroom", v))

        if context.soloist_activity > 0.78:
            v = -0.10
            score += v
            comp.append(("soloist_space", v))

    if gesture.role is GestureRole.SETUP:
        v = 0.36 * context.phrase_position
        score += v
        comp.append(("phrase_boundary", v))
        if context.section_transition:
            score += 0.32
            comp.append(("section_transition", 0.32))
        if context.harmonic_transition_confidence:
            v = 0.16 * context.harmonic_transition_confidence
            score += v
            comp.append(("shared_harmonic_transition", v))

    if "explicit_cue" in gesture.tags and context.requested_kick:
        score += 0.90
        comp.append(("explicit_ensemble_kick", 0.90))

    # Shared Harmony may inform structural intensity, but drum code never derives
    # scales, chord spellings, or functional theory itself.
    if context.harmony is not None:
        v = 0.08 * context.harmony.tension * (
            1.0 if gesture.role in {GestureRole.COMP, GestureRole.SETUP, GestureRole.ACCENT} else 0.25
        )
        score += v
        comp.append(("shared_tension_projection", v))

    return ScoredDrumGesture(gesture, score, tuple(comp))


def perform_one_gesture(
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
    memory: DrummerPerformanceMemory,
) -> ScoredDrumGesture:
    """Commit one immediate gesture. Caller must listen/re-plan after return."""
    plan.validate()
    context.validate()
    candidates = build_immediate_candidates(plan, context)
    chosen = max((score_gesture(g, plan, context) for g in candidates), key=lambda x: x.score)
    memory.commit(chosen.gesture)
    return chosen
