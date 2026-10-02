"""Shared corpus registry for RealSolo."""

from .registry import (
    CorpusAccess,
    CorpusItem,
    CorpusKind,
    CorpusRegistry,
    CorpusUse,
    RightsProfile,
    corpus_root_from_env,
)

__all__ = [
    "CorpusAccess",
    "CorpusItem",
    "CorpusKind",
    "CorpusRegistry",
    "CorpusUse",
    "RightsProfile",
    "corpus_root_from_env",
    "ALL_PLAYER_INSTRUMENTS",
    "IREALB_V1_DATASET_ID",
    "IREALB_V1_DOI",
    "IREALB_V1_LICENSE",
    "IREALB_V1_URL",
    "STANDARD_100_TITLES",
    "StandardChartInstallReport",
    "chart_item_id",
    "chart_relpath",
    "install_standard_100_from_archive",
    "register_standard_100",
    "standard_100_corpus_items",
]

from .standard_charts import (
    ALL_PLAYER_INSTRUMENTS,
    IREALB_V1_DATASET_ID,
    IREALB_V1_DOI,
    IREALB_V1_LICENSE,
    IREALB_V1_URL,
    STANDARD_100_TITLES,
    StandardChartInstallReport,
    chart_item_id,
    chart_relpath,
    install_standard_100_from_archive,
    register_standard_100,
    standard_100_corpus_items,
)
