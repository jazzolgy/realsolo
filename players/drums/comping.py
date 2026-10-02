"""Independent comping priors for the drum-set realization layer.

This module owns drummer-specific realization policy only.  It does not infer
Shared Core phrase/form/ensemble semantics; it consumes their projections.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import DrummerRuntimeContext, DrummerSoftPlan


@dataclass(frozen=True)
class CompingPropensity:
    snare: float
    bass_drum: float
    space: float

    def validate(self) -> None:
        for name in ("snare", "bass_drum", "space"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} propensity must be within 0..1")


def _clip(value: float) -> float:
    return min(1.0, max(0.0, value))


def comping_propensity(
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
) -> CompingPropensity:
    """Return independent snare/bass-drum/space propensities.

    Snare and bass drum are intentionally not one coupled boolean.  The values
    are candidate priors; the online evaluator still decides one immediate
    gesture using ensemble context and explicit cues.
    """
    plan.validate()
    context.validate()

    headroom = 1.0 - context.ensemble_activity
    soloist_room = 1.0 - 0.65 * context.soloist_activity
    density = plan.comping_density

    # Snare is more willing to answer/interject; bass drum is kept more
    # conservative unless energy or an explicit ensemble kick asks for it.
    snare = _clip(
        0.08
        + 0.56 * density
        + 0.18 * headroom
        + 0.10 * context.energy_target
    )
    bass = _clip(
        0.05
        + 0.38 * density
        + 0.15 * headroom
        + 0.16 * plan.energy
    )

    snare *= _clip(soloist_room + 0.18 * headroom)
    bass *= _clip(soloist_room + 0.10 * headroom)

    if context.requested_kick:
        bass = 1.0

    boundary = context.phrase_position >= 0.82 or context.section_transition
    if boundary:
        snare = _clip(snare + 0.16)
        bass = _clip(bass + 0.08)

    space = _clip(
        0.18
        + 0.52 * context.ensemble_activity
        + 0.28 * context.soloist_activity
        - 0.42 * density
    )

    result = CompingPropensity(snare, bass, space)
    result.validate()
    return result
