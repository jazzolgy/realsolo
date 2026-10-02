"""Policy that combines generator, evaluator, memory, and learned biases."""
from __future__ import annotations
from dataclasses import dataclass

from .evaluator import MotifEvaluation, MotifEvaluationContext, evaluate_motif
from .generator import MotifGenerationContext, generate_motif_candidates
from .learner import MotifLearningState
from .memory import MotifMemory
from .representation import MotifCandidate
from ..solo_grammar import SoloDevelopmentOperation


@dataclass(frozen=True)
class MotifPolicyDecision:
    candidate: MotifCandidate
    evaluation: MotifEvaluation
    development_operation: SoloDevelopmentOperation
    reasons: tuple[str, ...] = ()


def _operation_for(
    candidate: MotifCandidate,
    memory: MotifMemory | None,
    learning: MotifLearningState,
) -> SoloDevelopmentOperation:
    active = () if memory is None else memory.active()
    same = next((x for x in active if x.identity.motif_id == candidate.identity.motif_id), None)

    options = [
        SoloDevelopmentOperation.STATE,
        SoloDevelopmentOperation.VARY,
        SoloDevelopmentOperation.FRAGMENT,
        SoloDevelopmentOperation.SEQUENCE,
        SoloDevelopmentOperation.DISPLACE,
    ]
    if same is not None and same.usage_count >= 2:
        options.extend((SoloDevelopmentOperation.CONTRAST, SoloDevelopmentOperation.RECAP))

    base = {
        SoloDevelopmentOperation.STATE: .12,
        SoloDevelopmentOperation.VARY: .30,
        SoloDevelopmentOperation.FRAGMENT: .22,
        SoloDevelopmentOperation.SEQUENCE: .20,
        SoloDevelopmentOperation.DISPLACE: .18,
        SoloDevelopmentOperation.CONTRAST: .16,
        SoloDevelopmentOperation.RECAP: .18,
    }
    return max(options, key=lambda op: base[op] + .18 * learning.operation_bias(op))


def choose_motif_policy(
    generation_context: MotifGenerationContext,
    evaluation_context: MotifEvaluationContext,
    *,
    memory: MotifMemory | None = None,
    learning: MotifLearningState = MotifLearningState(),
) -> MotifPolicyDecision:
    candidates = generate_motif_candidates(generation_context, learning)
    if not candidates:
        raise ValueError("motif generator returned no candidates")

    scored = [(evaluate_motif(c, evaluation_context), c) for c in candidates]
    evaluation, candidate = max(scored, key=lambda pair: pair[0].total)
    operation = _operation_for(candidate, memory, learning)
    return MotifPolicyDecision(
        candidate=candidate,
        evaluation=evaluation,
        development_operation=operation,
        reasons=candidate.reasons + evaluation.reasons,
    )
