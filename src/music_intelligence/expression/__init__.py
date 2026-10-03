"""Shared expressive intelligence: HOW an already chosen event is realized."""
from .representation import (
    ExpressionContour,
    ExpressivePhase,
    RelativeExpressionProfile,
    ExpressiveContext,
    ExpressiveIntent,
)
from .engine import realize_expressive_intent

__all__=[
    "ExpressionContour",
    "ExpressivePhase",
    "RelativeExpressionProfile",
    "ExpressiveContext",
    "ExpressiveIntent",
    "realize_expressive_intent",
]
