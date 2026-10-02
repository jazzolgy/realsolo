"""Shared motif evaluation with development potential."""
from __future__ import annotations
from dataclasses import dataclass

from .representation import MotifCandidate


@dataclass(frozen=True)
class MotifEvaluationContext:
    harmonic_fit: float = .5
    ensemble_fit: float = .5
    novelty_need: float = .5
    coherence_need: float = .5
    recent_similarity: float = 0.0

    def validate(self) -> None:
        for name in (
            "harmonic_fit", "ensemble_fit", "novelty_need",
            "coherence_need", "recent_similarity",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


@dataclass(frozen=True)
class MotifEvaluation:
    total: float
    identity_clarity: float
    rhythmic_salience: float
    harmonic_flexibility: float
    transformability: float
    memorability: float
    interaction_potential: float
    redundancy_penalty: float
    reasons: tuple[str, ...] = ()


def evaluate_motif(
    candidate: MotifCandidate,
    context: MotifEvaluationContext,
) -> MotifEvaluation:
    candidate.validate()
    context.validate()
    ident = candidate.identity

    identity_clarity = min(1.0, .28 + .12 * len(ident.interval_schema) + .10 * len(ident.rhythm_schema))
    rhythmic_salience = min(1.0, .35 + .10 * len(set(ident.rhythm_schema))) if ident.rhythm_schema else .35
    harmonic_flexibility = .78 if ident.harmonic_target_behavior in {"contextual_retarget", "current_field"} else .62
    axes = sum(bool(x) for x in (
        ident.interval_schema, ident.rhythm_schema, ident.contour,
        ident.phrase_shape, ident.tension_shape, ident.interaction_function,
    ))
    transformability = min(1.0, .18 + .12 * axes)
    memorability = min(1.0, .30 + .18 * identity_clarity + .15 * rhythmic_salience)
    interaction_potential = .72 if ident.interaction_function else .45
    redundancy_penalty = context.recent_similarity * (.16 + .24 * context.novelty_need)

    total = (
        .15 * identity_clarity
        + .12 * rhythmic_salience
        + .13 * harmonic_flexibility
        + .20 * transformability
        + .12 * memorability
        + .10 * interaction_potential
        + .10 * context.harmonic_fit
        + .08 * context.ensemble_fit
        + .10 * candidate.generation_weight
        + .06 * candidate.learned_weight
        - redundancy_penalty
    )

    reasons = (
        "development potential rewards transformable identity",
        "evaluation preserves context fit over novelty alone",
    )
    return MotifEvaluation(
        total=total,
        identity_clarity=identity_clarity,
        rhythmic_salience=rhythmic_salience,
        harmonic_flexibility=harmonic_flexibility,
        transformability=transformability,
        memorability=memorability,
        interaction_potential=interaction_potential,
        redundancy_penalty=redundancy_penalty,
        reasons=reasons,
    )
