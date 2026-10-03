"""Bridge between motif identity and Shared Expressive Intelligence."""
from __future__ import annotations

from .engine import realize_expressive_intent
from .memory import MotifExpressionMemory
from .representation import ExpressiveContext, ExpressiveIntent, RelativeExpressionProfile


def expressive_intent_for_motif(
    motif_id: str,
    context: ExpressiveContext,
    *,
    memory: MotifExpressionMemory | None = None,
    profile: RelativeExpressionProfile | None = None,
) -> ExpressiveIntent:
    if not motif_id:
        raise ValueError("motif_id is required")
    resolved=context if memory is None else memory.contextualize(motif_id,context)
    return realize_expressive_intent(resolved,profile=profile)


def observe_committed_motif_expression(
    motif_id: str,
    intent: ExpressiveIntent,
    memory: MotifExpressionMemory,
    *,
    context: ExpressiveContext | None = None,
):
    """Commit expression memory after performance, never during candidate planning."""
    return memory.observe(
        motif_id,
        intent,
        position=None if context is None else context.position,
    )
