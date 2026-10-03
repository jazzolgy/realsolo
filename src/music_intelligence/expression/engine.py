"""Contextual shared expressive realization.

The engine deliberately keeps relative contour separate from absolute level:
the same stored phrase/vocabulary expression profile can be realized softly in
an already dense ensemble or expanded at a climax.

No future exact note sequence is scheduled here.
"""
from __future__ import annotations

from dataclasses import dataclass

from .representation import (
    ExpressiveContext,
    ExpressiveIntent,
    ExpressivePhase,
    ExpressionContour,
    RelativeExpressionProfile,
)


def _clamp(value: float, low: float=0.0, high: float=1.0) -> float:
    return max(low,min(high,value))


def _phase_relative(profile: RelativeExpressionProfile, phase: ExpressivePhase) -> float:
    if phase is ExpressivePhase.ENTRY:
        return profile.entry_relative
    if phase is ExpressivePhase.PEAK:
        return profile.peak_relative
    if phase in {ExpressivePhase.RELEASE,ExpressivePhase.AFTERGLOW}:
        return profile.release_relative
    # DEVELOP sits between entry and peak without assuming a mandatory crescendo.
    return (profile.entry_relative+profile.peak_relative)*0.5


def realize_expressive_intent(
    context: ExpressiveContext,
    *,
    profile: RelativeExpressionProfile | None = None,
) -> ExpressiveIntent:
    context.validate()
    if profile is not None:
        profile.validate()

    # Musical baseline: tension/climax can raise expressive energy, while dense
    # ensembles and release pressure can lower absolute level. These are bounded
    # contextual biases, not a rule that development must get louder.
    dynamic=.46
    dynamic += .16*(context.tension-.5)
    dynamic += .16*context.climax_pressure
    dynamic -= .14*max(0.0,context.ensemble_density-.55)
    dynamic -= .18*context.release_pressure

    accent=.46 + .10*context.tension + .08*context.boundary_pressure
    body=.52 + .10*(context.phrase_maturity-.5)
    foreground=context.target_foreground_weight
    timing=0.0
    contour=ExpressionContour.STABLE
    provenance=["shared_expressive_realization"]
    tags=set()

    if profile is not None:
        rel=_phase_relative(profile,context.expressive_phase)*profile.confidence
        dynamic += .22*rel
        accent += .16*profile.accent_bias*profile.confidence
        body += .18*profile.body_bias*profile.confidence
        foreground += .18*profile.foreground_bias*profile.confidence
        timing += profile.timing_bias_beats*profile.confidence
        contour=profile.contour
        provenance.extend(profile.provenance or (f"profile:{profile.profile_id}",))

    # Repetition variation: repeated material should not become an identical MIDI
    # stamp. Alternate small foreground/accent pressure without forcing louder.
    if context.repetition_index>0:
        if context.repetition_index % 3 == 1:
            accent += .04
            tags.add("repetition_accent_shift")
        elif context.repetition_index % 3 == 2:
            dynamic -= .04
            body += .04
            tags.add("repetition_dynamic_contrast")
        else:
            foreground += .04
            tags.add("repetition_foreground_shift")

    if context.release_pressure>=.65:
        body += .08
        accent -= .07
        tags.add("cadential_release")
    if context.climax_pressure>=.7:
        tags.add("climax_intent")
    if context.ensemble_density>=.75:
        tags.add("ensemble_level_reduced")

    # Perceptual intensity is related to but not identical with dynamic level.
    # Register and foreground role can make the same physical attack read as more
    # intense, so keep it a separate musical target for Players.
    perceptual=dynamic + .08*(context.register_height-.5) + .10*(foreground-.5)
    perceptual += .05*(accent-.5)

    out=ExpressiveIntent(
        perceptual_intensity=_clamp(perceptual),
        dynamic_level=_clamp(dynamic),
        accent_strength=_clamp(accent),
        note_body=_clamp(body),
        timing_emphasis_beats=max(-.5,min(.5,timing)),
        foreground_weight=_clamp(foreground),
        contour=contour,
        articulation_tags=frozenset(tags),
        confidence=profile.confidence if profile is not None else .75,
        provenance=tuple(provenance),
    )
    out.validate()
    return out
