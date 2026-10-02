"""Legend Intelligence: musician-specific evidence, memory, and conditional priors."""

from .interfaces import (
    LegendDomain,
    LegendProfileView,
    VocabularyMemoryItem,
    SignatureStatus,
    VocabularyQuery,
    VocabularyProvider,
    VocabularyUseType,
    VocabularyDimension,
)
from .mixture import ContextualLegendMixture, LegendViewWeight

__all__ = [
    "LegendDomain",
    "LegendProfileView",
    "VocabularyMemoryItem",
    "SignatureStatus",
    "VocabularyQuery",
    "VocabularyProvider",
    "VocabularyUseType",
    "VocabularyDimension",
    "ContextualLegendMixture",
    "LegendViewWeight",
]
