"""Shared feasibility contract for instrument realizations.

Core owns the assessment schema and evaluator protocol only.
Each Player owns the physical rules that produce the assessment.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

CandidateT = TypeVar("CandidateT")
ContextT = TypeVar("ContextT")


@dataclass(frozen=True)
class FeasibilityAssessment:
    feasible: bool
    cost: float = 0.0
    transition_cost: float = 0.0
    physical_conflict: float = 0.0
    confidence: float = 1.0
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        for name in ("cost", "transition_cost", "physical_conflict", "confidence"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


class FeasibilityEvaluator(Protocol, Generic[CandidateT, ContextT]):
    def __call__(self, candidate: CandidateT, context: ContextT) -> FeasibilityAssessment:
        ...
