"""Shared expressive intelligence: HOW an already chosen event is realized."""
from .representation import (
    ExpressionContour,
    ExpressivePhase,
    RelativeExpressionProfile,
    ExpressiveContext,
    ExpressiveIntent,
)
from .engine import realize_expressive_intent
from .memory import MotifExpressionMemory, MotifExpressionMemoryEntry
from .motif_bridge import expressive_intent_for_motif, observe_committed_motif_expression
from .solo_adapter import to_solo_expression_intent

__all__=[
    "ExpressionContour",
    "ExpressivePhase",
    "RelativeExpressionProfile",
    "ExpressiveContext",
    "ExpressiveIntent",
    "realize_expressive_intent",
    "MotifExpressionMemory",
    "MotifExpressionMemoryEntry",
    "expressive_intent_for_motif",
    "observe_committed_motif_expression",
    "to_solo_expression_intent",
]
