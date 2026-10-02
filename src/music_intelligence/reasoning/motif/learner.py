"""Incremental learning state for Shared Motif Generator.

This is intentionally lightweight and interpretable. It can later be replaced or
augmented by a learned model without changing the generator/policy contracts.
"""
from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Mapping

from .representation import MotifSourceType
from ..solo_grammar import SoloDevelopmentOperation


@dataclass(frozen=True)
class MotifFeedback:
    source_type: MotifSourceType
    operation: SoloDevelopmentOperation
    musical_fit: float
    memorability: float
    development_success: float
    ensemble_fit: float
    novelty: float
    coherence: float

    def validate(self) -> None:
        for name in (
            "musical_fit", "memorability", "development_success",
            "ensemble_fit", "novelty", "coherence",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")

    @property
    def reward(self) -> float:
        self.validate()
        return (
            .22 * self.musical_fit
            + .18 * self.memorability
            + .22 * self.development_success
            + .16 * self.ensemble_fit
            + .10 * self.novelty
            + .12 * self.coherence
        )


@dataclass(frozen=True)
class MotifLearningState:
    source_weights: Mapping[MotifSourceType, float] = field(default_factory=dict)
    operation_weights: Mapping[SoloDevelopmentOperation, float] = field(default_factory=dict)
    observations: int = 0
    learning_rate: float = .12

    def validate(self) -> None:
        if self.observations < 0:
            raise ValueError("observations may not be negative")
        if not 0.0 < self.learning_rate <= 1.0:
            raise ValueError("learning_rate must be within (0,1]")
        if any(not -1.0 <= v <= 1.0 for v in self.source_weights.values()):
            raise ValueError("source weights must be within -1..1")
        if any(not -1.0 <= v <= 1.0 for v in self.operation_weights.values()):
            raise ValueError("operation weights must be within -1..1")

    def source_bias(self, source: MotifSourceType) -> float:
        return self.source_weights.get(source, 0.0)

    def operation_bias(self, op: SoloDevelopmentOperation) -> float:
        return self.operation_weights.get(op, 0.0)


def update_motif_learning(
    state: MotifLearningState,
    feedback: MotifFeedback,
) -> MotifLearningState:
    state.validate()
    reward = feedback.reward
    centered = 2.0 * (reward - .5)

    source = dict(state.source_weights)
    operation = dict(state.operation_weights)
    lr = state.learning_rate

    old_source = source.get(feedback.source_type, 0.0)
    source[feedback.source_type] = max(-1.0, min(1.0, old_source + lr * (centered - old_source)))

    old_op = operation.get(feedback.operation, 0.0)
    operation[feedback.operation] = max(-1.0, min(1.0, old_op + lr * (centered - old_op)))

    out = replace(
        state,
        source_weights=source,
        operation_weights=operation,
        observations=state.observations + 1,
    )
    out.validate()
    return out
