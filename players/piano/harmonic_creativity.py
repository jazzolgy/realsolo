"""Adapt piano creative freedom from Shared Core harmonic reasoning.

High uncertainty does not automatically license aggressive reharmonization.
Harmonic-family freedom grows mainly when several credible current action options
coexist. Pure uncertainty instead loosens reversible realization dimensions.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.harmony.orchestrator import HarmonicReasoningResult

from .creative_continuity import CreativityContext, DimensionContinuityProfile


@dataclass(frozen=True)
class HarmonicCreativeFreedom:
    uncertainty: float
    option_diversity: float
    reversible_freedom: float
    harmonic_family_freedom: float

    def validate(self) -> None:
        for name in (
            "uncertainty",
            "option_diversity",
            "reversible_freedom",
            "harmonic_family_freedom",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


def assess_harmonic_creative_freedom(
    harmony: HarmonicReasoningResult | None,
) -> HarmonicCreativeFreedom:
    if harmony is None:
        return HarmonicCreativeFreedom(0.0, 0.0, 0.0, 0.0)

    credible = [
        option
        for option in harmony.action_options
        if option.confidence >= 0.55
        and option.interpretation_compatibility >= 0.50
    ]
    intents = {option.intent.value for option in credible}
    diversity = min(1.0, len(intents) / 4.0)

    uncertainty = max(0.0, min(1.0, harmony.uncertainty))
    reversible = uncertainty

    # Harmonic-family freedom needs actual plural compatible options.
    # Uncertainty alone is insufficient evidence for aggressive color changes.
    family = min(
        1.0,
        0.82 * diversity + 0.18 * diversity * uncertainty,
    )

    result = HarmonicCreativeFreedom(
        uncertainty=uncertainty,
        option_diversity=diversity,
        reversible_freedom=reversible,
        harmonic_family_freedom=family,
    )
    result.validate()
    return result


def adapt_continuity_profile_for_harmony(
    profile: DimensionContinuityProfile,
    harmony: HarmonicReasoningResult | None,
) -> DimensionContinuityProfile:
    profile.validate()
    freedom = assess_harmonic_creative_freedom(harmony)

    def loosen(value: float, amount: float, floor: float) -> float:
        return max(floor, min(1.0, value * (1.0 - amount)))

    return DimensionContinuityProfile(
        role=loosen(profile.role, 0.12 * freedom.harmonic_family_freedom, 0.12),
        family=loosen(profile.family, 0.38 * freedom.harmonic_family_freedom, 0.08),
        rhythm=loosen(profile.rhythm, 0.10 * freedom.reversible_freedom, 0.10),
        register=loosen(profile.register, 0.28 * freedom.reversible_freedom, 0.05),
        dynamic=loosen(profile.dynamic, 0.30 * freedom.reversible_freedom, 0.04),
        touch=loosen(profile.touch, 0.30 * freedom.reversible_freedom, 0.04),
    )


def adapt_creativity_context_for_harmony(
    context: CreativityContext,
    harmony: HarmonicReasoningResult | None,
) -> CreativityContext:
    context.validate()
    freedom = assess_harmonic_creative_freedom(harmony)

    strength = min(
        1.0,
        context.creativity_strength
        * (
            1.0
            + 0.12 * freedom.reversible_freedom
            + 0.16 * freedom.harmonic_family_freedom
        ),
    )
    floor = max(
        0.18,
        context.coherence_floor
        * (1.0 - 0.18 * freedom.harmonic_family_freedom),
    )

    if harmony is not None and harmony.needs_more_evidence:
        floor = max(floor, 0.28)

    return CreativityContext(
        creativity_strength=strength,
        coherence_floor=floor,
    )
