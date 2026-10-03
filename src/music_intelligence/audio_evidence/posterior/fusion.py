"""Bounded contextual posterior updates that preserve raw detector evidence."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

from ..context.models import ContextEvidence
from ..observation.models import AudioObservation


def _normalize(values: Mapping[str, float]) -> dict[str, float]:
    total = sum(values.values())
    if total <= 0.0:
        raise ValueError("probability mass must be positive")
    return {key: value / total for key, value in values.items()}


@dataclass(frozen=True)
class AppliedContextFactor:
    factor_id: str
    source: str
    weight: float


@dataclass(frozen=True)
class PosteriorRevision:
    factor_ids: tuple[str, ...]
    reason: str
    applied_factors: tuple[AppliedContextFactor, ...] = ()
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextualAudioHypothesis:
    observation: AudioObservation
    instrument_posterior: Mapping[str, float]
    role_posterior: Mapping[str, float]
    revision: PosteriorRevision | None = None

    @property
    def instrument_ranking(self) -> tuple[tuple[str, float], ...]:
        return tuple(
            sorted(
                self.instrument_posterior.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )


class BoundedContextPosterior:
    """Apply context without allowing it to erase acoustic evidence."""

    def __init__(self, max_context_log_shift: float = 1.75):
        if max_context_log_shift <= 0.0:
            raise ValueError("max_context_log_shift must be positive")
        self.max_context_log_shift = float(max_context_log_shift)

    def revise_instrument(
        self,
        observation: AudioObservation,
        factors: Sequence[ContextEvidence] = (),
    ) -> ContextualAudioHypothesis:
        observation = observation.normalized()
        prior = dict(observation.instrument_probabilities)
        if not prior:
            return ContextualAudioHypothesis(
                observation=observation,
                instrument_posterior={},
                role_posterior=dict(observation.role_probabilities),
            )

        shifts = {key: 0.0 for key in prior}
        used: list[str] = []
        applied_factors: list[AppliedContextFactor] = []
        for factor in factors:
            factor.validate()
            overlapping = [key for key in prior if key in factor.likelihoods]
            if not overlapping:
                continue
            logs = [math.log(float(factor.likelihoods[key])) for key in overlapping]
            center = sum(logs) / len(logs)
            for key in overlapping:
                shifts[key] += factor.weight * (
                    math.log(float(factor.likelihoods[key])) - center
                )
            used.append(factor.factor_id)
            applied_factors.append(
                AppliedContextFactor(
                    factor_id=factor.factor_id,
                    source=factor.source,
                    weight=factor.weight,
                )
            )

        clipped = {
            key: max(
                -self.max_context_log_shift,
                min(self.max_context_log_shift, shift),
            )
            for key, shift in shifts.items()
        }
        logits = {
            key: math.log(max(probability, 1e-12)) + clipped[key]
            for key, probability in prior.items()
        }
        anchor = max(logits.values())
        posterior = _normalize(
            {key: math.exp(value - anchor) for key, value in logits.items()}
        )

        revision = None
        if used:
            revision = PosteriorRevision(
                factor_ids=tuple(used),
                reason="bounded context adjustment of raw instrument probabilities",
                applied_factors=tuple(applied_factors),
                provenance=("audio-evidence:bounded-context-posterior",),
            )

        return ContextualAudioHypothesis(
            observation=observation,
            instrument_posterior=posterior,
            role_posterior=dict(observation.role_probabilities),
            revision=revision,
        )
