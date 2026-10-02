"""Constraint-aware creative correction for the piano comping evaluator."""
from __future__ import annotations

from dataclasses import replace

from .comping import PianoCompingEvaluator, PianoCompingScore
from .creative_continuity import (
    CreativityContext,
    evaluate_creative_continuity,
    profile_from_harmonic_context,
)
from .harmonic_creativity import (
    adapt_continuity_profile_for_harmony,
    adapt_creativity_context_for_harmony,
)
from .constraint_creativity import adapt_profile_for_ensemble_context


class ConstraintAwarePianoCompingEvaluator(PianoCompingEvaluator):
    """Keep creativity active by moving it onto contextually available dimensions."""

    def evaluate(
        self,
        candidate,
        comping_context,
        musical_context,
        state,
        harmonic_affordance=None,
        interaction_state=None,
        harmonic_reasoning=None,
    ) -> PianoCompingScore:
        base = super().evaluate(
            candidate,
            comping_context,
            musical_context,
            state,
            harmonic_affordance,
            interaction_state,
            harmonic_reasoning,
        )

        previous = state.recent_signatures[-1] if state.recent_signatures else None
        profile = profile_from_harmonic_context(state.last_harmonic_continuity)
        profile = adapt_continuity_profile_for_harmony(profile, harmonic_reasoning)

        creativity_context = adapt_creativity_context_for_harmony(
            CreativityContext(
                creativity_strength=comping_context.creativity_strength,
                coherence_floor=comping_context.creativity_coherence_floor,
            ),
            harmonic_reasoning,
        )

        unconstrained = evaluate_creative_continuity(
            candidate,
            previous,
            profile,
            creativity_context,
        )
        constrained_profile = adapt_profile_for_ensemble_context(
            profile,
            comping_context,
        )
        constrained = evaluate_creative_continuity(
            candidate,
            previous,
            constrained_profile,
            creativity_context,
        )

        delta = constrained.total - unconstrained.total
        if delta == 0:
            return base

        components = dict(base.components)
        components["constraint_creativity_adjustment"] = delta
        for key, value in constrained.components.items():
            components[f"constraint_creativity:{key}"] = value

        return replace(
            base,
            total=base.total + delta,
            components=components,
            reasons=base.reasons + constrained.reasons,
        )
