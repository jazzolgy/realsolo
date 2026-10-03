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
    "VocabularyPromotionDecision",
    "VocabularyPromotionEvidence",
    "VocabularyPromotionStatus",
    "active_runtime_items",
    "assess_vocabulary_promotion",
]


from .promotion import (
    VocabularyPromotionDecision,
    VocabularyPromotionEvidence,
    VocabularyPromotionStatus,
    active_runtime_items,
    assess_vocabulary_promotion,
)
