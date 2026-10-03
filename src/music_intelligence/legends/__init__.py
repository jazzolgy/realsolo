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
from .data_policy import (
    LegendDataLayer,
    LegendMaterialKind,
    PrivateLegendStoreDescriptor,
    PrivateLegendVocabularyProvider,
    default_legend_data_layer,
    may_publish_material,
)

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
    "LegendDataLayer",
    "LegendMaterialKind",
    "PrivateLegendStoreDescriptor",
    "PrivateLegendVocabularyProvider",
    "default_legend_data_layer",
    "may_publish_material",
]
