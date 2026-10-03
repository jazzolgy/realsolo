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
    ScorePerformancePhase,
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
    "ScorePerformancePhase",
    "ScorePosition",
    "ScoreSpan",
    "StructuredScoreEvidence",
    "resolve_score_context",
    "structured_evidence_from_locator",
]


from .songs import (
    ALONG_CAME_BETTY_EVIDENCE,
    ALONG_CAME_BETTY_LOCATOR,
    along_came_betty_evidence,
)

__all__ += [
    "ALONG_CAME_BETTY_EVIDENCE",
    "ALONG_CAME_BETTY_LOCATOR",
    "along_came_betty_evidence",
]


from .realchord import (
    ExpectedHarmonyReference,
    REALCHORD_1350_DATASET_ID,
    REALCHORD_1350_DEFAULT_RELPATH,
    RealChordChord,
    RealChordMeasure,
    RealChordSong,
    coordinate_from_realchord,
    expected_harmony_at,
    realchord_1350_corpus_item,
    register_realchord_1350,
    song_from_normalized_record,
)

__all__ += [
    "ExpectedHarmonyReference",
    "REALCHORD_1350_DATASET_ID",
    "REALCHORD_1350_DEFAULT_RELPATH",
    "RealChordChord",
    "RealChordMeasure",
    "RealChordSong",
    "coordinate_from_realchord",
    "expected_harmony_at",
    "realchord_1350_corpus_item",
    "register_realchord_1350",
    "song_from_normalized_record",
]


from .realchord_parser import (
    decode_progression,
    parse_playlist_html,
    parse_progression,
    parse_song_body,
    realchord_id,
)

from .realchord_runtime import (
    RealChordPlaybackMeasure,
    RealChordPlaybackTimeline,
    SharedRealChordSessionState,
    expand_playback_timeline,
    expected_harmony_for_state,
    future_harmony,
    session_state_at,
)

__all__ += [
    "decode_progression",
    "parse_playlist_html",
    "parse_progression",
    "parse_song_body",
    "realchord_id",
    "RealChordPlaybackMeasure",
    "RealChordPlaybackTimeline",
    "SharedRealChordSessionState",
    "expand_playback_timeline",
    "expected_harmony_for_state",
    "future_harmony",
    "session_state_at",
]


from .realchord_library import (
    RealChordLibrary,
    library_from_normalized_corpus,
    load_realchord_library,
)

__all__ += [
    "RealChordLibrary",
    "library_from_normalized_corpus",
    "load_realchord_library",
]
