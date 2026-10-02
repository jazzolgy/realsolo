"""v1.35 contextual tension model.

A pitch can be a melodic scale/approach tone, a melodic tension, a harmonic
tension, or an exposed conflict depending on role and context. Availability is
multi-dimensional rather than a single allowed/avoid boolean.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MusicalLayer(str, Enum):
    MELODY = "melody"
    SUPPORTING_HARMONY = "supporting_harmony"
    BASS = "bass"
    INNER_VOICE = "inner_voice"
    UNKNOWN = "unknown"


class TensionUse(str, Enum):
    CHORD_TONE = "chord_tone"
    SCALE_APPROACH = "scale_approach"
    MELODIC_TENSION = "melodic_tension"
    HARMONIC_TENSION = "harmonic_tension"
    CONTEXTUAL_COLOR = "contextual_color"
    EXPOSED_CONFLICT = "exposed_conflict"


@dataclass(frozen=True)
class TensionContext:
    layer: MusicalLayer
    is_chord_tone: bool = False
    is_nonbasic_scale_tone: bool = False
    included_in_chord_symbol: bool = False
    altered: bool = False
    duration_beats: float = 0.0
    strong_metric_position: bool = False
    followed_by_step_to_chord_tone: bool = False
    followed_by_leap: bool = False
    exposed: bool = False
    register_sensitive: bool = False
    modal_context: bool = False
    characteristic_modal_tone: bool = False
    explicit_arrangement_tension: bool = False


@dataclass(frozen=True)
class TensionAssessment:
    use: TensionUse
    melodic_availability: float
    harmonic_support_availability: float
    exposure_sensitivity: float
    metric_sensitivity: float
    register_sensitivity: float
    resolution_need: float
    reasons: tuple[str, ...] = ()


def assess_tension(ctx: TensionContext) -> TensionAssessment:
    if ctx.duration_beats < 0:
        raise ValueError("duration_beats may not be negative")

    if ctx.is_chord_tone:
        return TensionAssessment(
            TensionUse.CHORD_TONE, 1.0, 1.0, .05, .05,
            .15 if ctx.register_sensitive else .05, .05,
            ("basic chord tone",),
        )

    melodic = .55
    harmonic = .35
    exposure = .45
    metric = .35
    register = .45 if ctx.register_sensitive else .20
    resolution = .45
    reasons: list[str] = []

    if ctx.is_nonbasic_scale_tone and ctx.followed_by_step_to_chord_tone:
        melodic += .28
        harmonic -= .12
        resolution += .12
        reasons.append("stepwise approach use supports melody more than accompaniment")

    melodic_tension = (
        ctx.layer is MusicalLayer.MELODY
        and (
            ctx.duration_beats > 1.0
            or ctx.followed_by_leap
            or (ctx.strong_metric_position and ctx.followed_by_step_to_chord_tone)
        )
    )
    if melodic_tension:
        use = TensionUse.MELODIC_TENSION
        melodic += .18
        metric += .15 if ctx.strong_metric_position else 0.0
        resolution += .10
        reasons.append("melodic tension conditions")
    elif ctx.layer in {MusicalLayer.SUPPORTING_HARMONY, MusicalLayer.INNER_VOICE}:
        use = TensionUse.HARMONIC_TENSION
    elif ctx.is_nonbasic_scale_tone:
        use = TensionUse.SCALE_APPROACH
    else:
        use = TensionUse.CONTEXTUAL_COLOR

    if ctx.included_in_chord_symbol or ctx.explicit_arrangement_tension:
        harmonic += .38
        exposure -= .12
        reasons.append("explicit harmonic tension")

    if ctx.altered and ctx.layer in {MusicalLayer.SUPPORTING_HARMONY, MusicalLayer.INNER_VOICE}:
        if ctx.included_in_chord_symbol or ctx.explicit_arrangement_tension:
            harmonic += .08
            reasons.append("altered supporting tension explicitly specified")
        else:
            harmonic -= .18
            exposure += .18
            reasons.append("unspecified altered supporting tension requires caution")

    if ctx.modal_context and ctx.characteristic_modal_tone:
        melodic += .15
        harmonic += .12
        resolution -= .15
        reasons.append("modal characteristic tone")

    if ctx.exposed:
        exposure += .20
        if not (ctx.included_in_chord_symbol or ctx.characteristic_modal_tone):
            harmonic -= .10
            reasons.append("exposed nonbasic tone")

    melodic = min(1.0, max(0.0, melodic))
    harmonic = min(1.0, max(0.0, harmonic))
    exposure = min(1.0, max(0.0, exposure))
    metric = min(1.0, max(0.0, metric))
    register = min(1.0, max(0.0, register))
    resolution = min(1.0, max(0.0, resolution))

    if harmonic < .20 and ctx.exposed:
        use = TensionUse.EXPOSED_CONFLICT

    return TensionAssessment(
        use,
        melodic,
        harmonic,
        exposure,
        metric,
        register,
        resolution,
        tuple(reasons),
    )
