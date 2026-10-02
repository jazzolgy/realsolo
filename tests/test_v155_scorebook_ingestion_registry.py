from music_intelligence.corpus import (
    CorpusRegistry,
    SCOREBOOK_SPECS,
    SEED_SONG_LOCATORS,
    ScoreEvidenceKind,
    ScoreIngestStatus,
    ingestion_queue,
    register_scorebooks,
    scorebook_corpus_items,
    songs_for_book,
    validate_song_locators,
)


def test_nine_scorebooks_are_registered_once():
    assert len(SCOREBOOK_SPECS) == 9
    assert len({x.book_id for x in SCOREBOOK_SPECS}) == 9
    assert len({x.filename for x in SCOREBOOK_SPECS}) == 9


def test_scorebooks_are_shared_private_core_sources():
    items = scorebook_corpus_items()
    assert len(items) == 9
    for item in items:
        assert "shared_core" in item.tags
        assert item.access.value == "project_private"
        assert item.rights.redistribution_permission is False
        assert "bass" in item.instruments
        assert "piano" in item.instruments
        assert "drums" in item.instruments
        assert "transcribe" in item.instruments


def test_seed_locators_reference_known_books():
    validate_song_locators(SEED_SONG_LOCATORS)
    assert any(x.title == "Autumn Leaves" for x in SEED_SONG_LOCATORS)


def test_realbook_alfies_theme_retains_feel_change_evidence():
    song = next(x for x in SEED_SONG_LOCATORS if x.title == "Alfie's Theme")
    values = {e.value for e in song.evidence if e.kind is ScoreEvidenceKind.FEEL_CHANGE}
    assert {"two feel", "in four", "back to 2"} <= values


def test_newreal2_contains_bass_specific_seed_evidence():
    songs = songs_for_book("scorebook.newreal.2")
    assert any(
        any(e.kind is ScoreEvidenceKind.WRITTEN_BASS_PART for e in song.evidence)
        for song in songs
    )


def test_queue_keeps_reviewed_pages_until_structured_and_verified():
    queue = ingestion_queue(SEED_SONG_LOCATORS)
    assert queue
    assert all(x.status is ScoreIngestStatus.VISION_REVIEWED for x in queue)


def test_registry_can_hold_nine_books_with_existing_core_sources():
    registry = CorpusRegistry()
    register_scorebooks(registry)
    assert len(registry.query(tag="scorebook")) == 9
