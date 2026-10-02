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
]


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
]
