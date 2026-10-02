from __future__ import annotations

from .creative_continuity import DimensionContinuityProfile


def adapt_profile_for_ensemble_context(profile, context):
    profile.validate()

    role = profile.role
    family = profile.family
    rhythm = profile.rhythm
    register = profile.register
    dynamic = profile.dynamic
    touch = profile.touch

    busy = getattr(context, "soloist_activity", 0.5) >= 0.72
    crowded = getattr(context, "ensemble_density", 0.5) >= 0.72
    phrase_open = (
        getattr(context, "phrase_boundary_probability", 0.0) >= 0.65
        and getattr(context, "available_space_beats", 0.0) >= 0.5
    )

    occupancy = getattr(context, "role_occupancy", None)
    priority = getattr(getattr(occupancy, "priority", None), "value", "")
    harmonic_coverage = getattr(occupancy, "other_harmonic_coverage", 0.0)
    rhythmic_coverage = getattr(occupancy, "other_rhythmic_coverage", 0.0)
    agreement = getattr(occupancy, "harmonic_agreement_confidence", 1.0)

    if busy:
        rhythm *= 0.88
        register *= 0.66
        dynamic *= 0.58
        touch *= 0.62

    if crowded:
        register *= 0.75
        dynamic *= 0.62
        touch *= 0.68

    if phrase_open:
        role *= 0.72
        rhythm *= 0.70

    coverage = max(harmonic_coverage, rhythmic_coverage)
    if priority == "other_primary" and coverage >= 0.6:
        rhythm *= 0.68
        register *= 0.62
        dynamic *= 0.70
        touch *= 0.60
        family = min(1.0, family + 0.08 * harmonic_coverage)

    if priority == "shared" and coverage >= 0.7:
        rhythm *= 0.78
        register *= 0.72
        dynamic *= 0.70
        touch *= 0.72

    if agreement < 0.5:
        family = min(1.0, family + 0.30 * (1.0 - agreement))
        register *= 0.82
        dynamic *= 0.82
        touch *= 0.82

    return DimensionContinuityProfile(
        role=max(0.05, min(1.0, role)),
        family=max(0.05, min(1.0, family)),
        rhythm=max(0.05, min(1.0, rhythm)),
        register=max(0.03, min(1.0, register)),
        dynamic=max(0.03, min(1.0, dynamic)),
        touch=max(0.03, min(1.0, touch)),
    )
