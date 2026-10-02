"""Bebop ride-continuity model.

The ride cymbal is modeled as a persistent time-bearing field with a variable
surface, not as a repeated two-beat MIDI loop.

This module owns only drummer-specific ride realization.  It consumes current
clock position, bebop interaction state, bass-pulse projection, and local ride
execution history.  It does not redefine Shared Core time/form semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .bass_coupling import BassPulseProjection, infer_bass_drums_coupling
from .bebop import BebopInteractionState
from .bebop_profile import BebopStyleProfile, DEFAULT_BEBOP_PROFILE
from .model import (
    DrumGesture,
    DrumHit,
    DrummerRuntimeContext,
    DrummerSoftPlan,
    DrumVoice,
    GestureRole,
    Limb,
)
from .timing import (
    bounded_timing_offset_ms,
    tempo_conditioned_swing_prior,
)


class RidePhase(str, Enum):
    QUARTER = "quarter"
    SKIP = "skip"
    OTHER = "other"


class RideSurfaceAction(str, Enum):
    HOLD_QUARTER = "hold_quarter"
    LIFT_SKIP = "lift_skip"
    OMIT_SKIP = "omit_skip"
    ACCENT_QUARTER = "accent_quarter"
    ACCENT_SKIP = "accent_skip"
    RELAX_SURFACE = "relax_surface"
    REASSERT_TIME = "reassert_time"


@dataclass(frozen=True)
class RideContinuityMemory:
    recent_quarter_hits: int = 0
    recent_quarter_omissions: int = 0
    recent_skip_hits: int = 0
    recent_skip_omissions: int = 0
    beats_since_clear_quarter: float = 0.0
    last_action: RideSurfaceAction | None = None

    def validate(self) -> None:
        for name in (
            "recent_quarter_hits",
            "recent_quarter_omissions",
            "recent_skip_hits",
            "recent_skip_omissions",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} may not be negative")
        if self.beats_since_clear_quarter < 0:
            raise ValueError("beats_since_clear_quarter may not be negative")


@dataclass(frozen=True)
class RideCandidate:
    gesture: DrumGesture
    action: RideSurfaceAction
    score_bias: float
    reasons: tuple[str, ...]


def classify_ride_phase(
    context: DrummerRuntimeContext,
    *,
    tolerance_beats: float = 0.045,
) -> RidePhase:
    """Classify only the current decision instant."""
    prior = tempo_conditioned_swing_prior(context.tempo_bpm)
    phase = context.position_in_bar_beats % 1.0

    if min(abs(phase), abs(phase - 1.0)) <= tolerance_beats:
        return RidePhase.QUARTER
    if abs(phase - prior.offbeat_fraction) <= tolerance_beats:
        return RidePhase.SKIP
    return RidePhase.OTHER


def _context_ride_hit(
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
    *,
    velocity_delta: int = 0,
    articulation: str = "tip",
) -> DrumHit:
    prior = tempo_conditioned_swing_prior(context.tempo_bpm)
    return DrumHit(
        DrumVoice.RIDE,
        Limb.RIGHT_HAND,
        velocity=max(1, min(127, plan.ride_velocity + velocity_delta)),
        microtiming_ms=bounded_timing_offset_ms(
            plan.microtiming_bias_ms,
            prior.ride_bias_ms,
            plan.expressive_timing_offset_ms,
            prior,
        ),
        articulation=articulation,
    )


def build_ride_candidates(
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
    interaction: BebopInteractionState,
    memory: RideContinuityMemory,
    *,
    bass: BassPulseProjection | None = None,
    profile: BebopStyleProfile = DEFAULT_BEBOP_PROFILE,
) -> tuple[RideCandidate, ...]:
    """Build immediate ride-surface alternatives for the current instant."""
    plan.validate()
    context.validate()
    memory.validate()
    profile.validate()

    phase = classify_ride_phase(context)
    if phase is RidePhase.OTHER:
        return ()

    coupling = None
    if bass is not None:
        bass.validate()
        coupling = infer_bass_drums_coupling(
            bass,
            interaction_state=interaction,
        )

    out: list[RideCandidate] = []

    if phase is RidePhase.QUARTER:
        out.append(RideCandidate(
            DrumGesture(
                hits=(_context_ride_hit(plan, context, articulation="tip"),),
                role=GestureRole.TIME,
                tags=frozenset({"bebop", "ride_continuity", "quarter", "hold_quarter"}),
                provenance=("drum_player", "ride_continuity"),
            ),
            RideSurfaceAction.HOLD_QUARTER,
            0.34 * profile.ride_time_salience.value,
            ("quarter-note forward motion",),
        ))

        accent_reason = interaction in {
            BebopInteractionState.BUILD,
            BebopInteractionState.HANDOFF,
        } or context.phrase_position >= 0.88
        if accent_reason:
            out.append(RideCandidate(
                DrumGesture(
                    hits=(_context_ride_hit(
                        plan, context, velocity_delta=12, articulation="accent_tip"
                    ),),
                    role=GestureRole.TIME,
                    tags=frozenset({"bebop", "ride_continuity", "quarter", "accent_quarter"}),
                    provenance=("drum_player", "ride_continuity"),
                ),
                RideSurfaceAction.ACCENT_QUARTER,
                0.26,
                ("interaction/form supports a stronger quarter",),
            ))

        # A quarter omission is represented only as an emergency/relax option
        # and strongly penalized if the drummer has recently omitted quarters.
        omission_bias = -0.46 - 0.18 * memory.recent_quarter_omissions
        if coupling is not None and coupling.shared_pulse >= 0.78:
            omission_bias += 0.20 * coupling.shared_pulse
        if interaction is BebopInteractionState.COAST:
            omission_bias += 0.08
        out.append(RideCandidate(
            DrumGesture(
                role=GestureRole.SPACE,
                tags=frozenset({"bebop", "ride_continuity", "quarter_omission", "relax_surface"}),
                provenance=("drum_player", "ride_continuity"),
            ),
            RideSurfaceAction.RELAX_SURFACE,
            omission_bias,
            ("quarter omission is exceptional; bass floor may make it safer",),
        ))

        if memory.beats_since_clear_quarter >= 1.5 or memory.recent_quarter_omissions >= 1:
            out.append(RideCandidate(
                DrumGesture(
                    hits=(_context_ride_hit(
                        plan, context, velocity_delta=8, articulation="reassert_time"
                    ),),
                    role=GestureRole.TIME,
                    tags=frozenset({"bebop", "ride_continuity", "reassert_time"}),
                    provenance=("drum_player", "ride_continuity"),
                ),
                RideSurfaceAction.REASSERT_TIME,
                0.48,
                ("recent ride surface was ambiguous; restore quarter-note clarity",),
            ))

    elif phase is RidePhase.SKIP:
        out.append(RideCandidate(
            DrumGesture(
                hits=(_context_ride_hit(
                    plan, context, velocity_delta=-2, articulation="skip_tip"
                ),),
                role=GestureRole.TIME,
                tags=frozenset({"bebop", "ride_continuity", "skip", "lift_skip"}),
                provenance=("drum_player", "ride_continuity"),
            ),
            RideSurfaceAction.LIFT_SKIP,
            0.22 * (1.0 - 0.35 * profile.skip_surface_flexibility.value),
            ("classic skip-note lift remains available",),
        ))

        omit_bias = 0.12 + 0.36 * profile.skip_surface_flexibility.value
        if interaction in {
            BebopInteractionState.COAST,
            BebopInteractionState.COME_DOWN,
            BebopInteractionState.LISTEN,
        }:
            omit_bias += 0.14
        if memory.recent_skip_omissions >= 2:
            omit_bias -= 0.18
        out.append(RideCandidate(
            DrumGesture(
                role=GestureRole.SPACE,
                tags=frozenset({"bebop", "ride_continuity", "omit_skip"}),
                provenance=("drum_player", "ride_continuity"),
            ),
            RideSurfaceAction.OMIT_SKIP,
            omit_bias,
            ("skip surface is flexible and may be omitted without losing deep pulse",),
        ))

        if interaction in {
            BebopInteractionState.BUILD,
            BebopInteractionState.HANDOFF,
        } or context.phrase_position >= 0.9:
            out.append(RideCandidate(
                DrumGesture(
                    hits=(_context_ride_hit(
                        plan, context, velocity_delta=10, articulation="accent_skip"
                    ),),
                    role=GestureRole.TIME,
                    tags=frozenset({"bebop", "ride_continuity", "skip", "accent_skip"}),
                    provenance=("drum_player", "ride_continuity"),
                ),
                RideSurfaceAction.ACCENT_SKIP,
                0.24,
                ("skip accent can lift phrase energy or punctuation",),
            ))

    for candidate in out:
        candidate.gesture.validate()
    return tuple(out)


def update_ride_memory(
    memory: RideContinuityMemory,
    action: RideSurfaceAction,
    phase: RidePhase,
) -> RideContinuityMemory:
    """Update local execution memory after one committed ride action."""
    memory.validate()

    q_hits = memory.recent_quarter_hits
    q_omit = memory.recent_quarter_omissions
    s_hits = memory.recent_skip_hits
    s_omit = memory.recent_skip_omissions
    since_q = memory.beats_since_clear_quarter

    if phase is RidePhase.QUARTER:
        if action in {
            RideSurfaceAction.HOLD_QUARTER,
            RideSurfaceAction.ACCENT_QUARTER,
            RideSurfaceAction.REASSERT_TIME,
        }:
            q_hits = min(8, q_hits + 1)
            q_omit = 0
            since_q = 0.0
        else:
            q_omit = min(8, q_omit + 1)
            q_hits = max(0, q_hits - 1)
            since_q += 1.0
    elif phase is RidePhase.SKIP:
        since_q += 0.5
        if action in {
            RideSurfaceAction.LIFT_SKIP,
            RideSurfaceAction.ACCENT_SKIP,
        }:
            s_hits = min(8, s_hits + 1)
            s_omit = max(0, s_omit - 1)
        elif action is RideSurfaceAction.OMIT_SKIP:
            s_omit = min(8, s_omit + 1)
            s_hits = max(0, s_hits - 1)

    return RideContinuityMemory(
        recent_quarter_hits=q_hits,
        recent_quarter_omissions=q_omit,
        recent_skip_hits=s_hits,
        recent_skip_omissions=s_omit,
        beats_since_clear_quarter=since_q,
        last_action=action,
    )


def score_ride_surface_gesture(
    gesture: DrumGesture,
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
    interaction: BebopInteractionState,
    memory: RideContinuityMemory,
    *,
    bass: BassPulseProjection | None = None,
    profile: BebopStyleProfile = DEFAULT_BEBOP_PROFILE,
) -> float:
    """Recover the current ride-surface candidate bias by musical identity."""
    candidates = build_ride_candidates(
        plan,
        context,
        interaction,
        memory,
        bass=bass,
        profile=profile,
    )
    tags = gesture.tags
    for candidate in candidates:
        action_tag = candidate.action.value
        if action_tag in tags:
            return candidate.score_bias
    return 0.0
