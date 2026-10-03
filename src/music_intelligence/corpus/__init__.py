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
    "IREALB_V1_ARCHIVE_URL",
    "IREALB_V1_DATASET_ID",
    "IREALB_V1_DOI",
    "IREALB_V1_LICENSE",
    "IREALB_V1_URL",
    "STANDARD_100_TITLES",
    "StandardChartInstallReport",
    "chart_item_id",
    "chart_relpath",
    "download_and_install_standard_100",
    "install_standard_100_from_archive",
    "register_standard_100",
    "standard_100_corpus_items",
]

from .standard_charts import (
    ALL_PLAYER_INSTRUMENTS,
    IREALB_V1_ARCHIVE_URL,
    IREALB_V1_DATASET_ID,
    IREALB_V1_DOI,
    IREALB_V1_LICENSE,
    IREALB_V1_URL,
    STANDARD_100_TITLES,
    StandardChartInstallReport,
    chart_item_id,
    chart_relpath,
    download_and_install_standard_100,
    install_standard_100_from_archive,
    register_standard_100,
    standard_100_corpus_items,
)

from .scorebooks import (
    SCOREBOOK_SPECS,
    SEED_SONG_LOCATORS,
    ScoreEvidence,
    ScoreEvidenceKind,
    ScoreIngestStatus,
    ScorebookFamily,
    ScorebookSongLocator,
    ScorebookSpec,
    ingestion_queue,
    register_scorebooks,
    scorebook_corpus_items,
    songs_for_book,
    validate_song_locators,
)


from .score_context import (
    ScoreContextSnapshot,
    ScorePosition,
    ScoreSpan,
    StructuredScoreEvidence,
    resolve_score_context,
    structured_evidence_from_locator,
)

__all__ += [
    "SCOREBOOK_SPECS",
    "SEED_SONG_LOCATORS",
    "ScoreEvidence",
    "ScoreEvidenceKind",
    "ScoreIngestStatus",
    "ScorebookFamily",
    "ScorebookSongLocator",
    "ScorebookSpec",
    "ingestion_queue",
    "register_scorebooks",
    "scorebook_corpus_items",
    "songs_for_book",
    "validate_song_locators",
    "ScoreContextSnapshot",
    "ScorePosition",
    "ScoreSpan",
    "StructuredScoreEvidence",
    "resolve_score_context",
    "structured_evidence_from_locator",
]


from .form_sources import (
    FORM_SOURCE_TAGS,
    FormSourceCandidate,
    discover_form_sources,
)

__all__ += [
    "FORM_SOURCE_TAGS",
    "FormSourceCandidate",
    "discover_form_sources",
]
