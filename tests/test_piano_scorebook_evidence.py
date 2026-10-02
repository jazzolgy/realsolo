from music_intelligence.corpus import (
    SEED_SONG_LOCATORS,
    ScoreEvidence,
    ScoreEvidenceKind,
    ScoreIngestStatus,
    ScorebookSongLocator,
)
from players.piano import build_piano_scorebook_evidence_view


def test_piano_consumes_canonical_alfies_theme_feel_changes():
    song=next(x for x in SEED_SONG_LOCATORS if x.title=="Alfie's Theme")
    view=build_piano_scorebook_evidence_view(song)
    assert {"two feel","in four","back to 2"} <= set(view.feel_changes)
    assert view.book_id=="scorebook.real.2"


def test_piano_does_not_treat_bass_specific_seed_as_piano_written_part():
    song=next(x for x in SEED_SONG_LOCATORS if x.title=="Along Came Betty")
    view=build_piano_scorebook_evidence_view(song)
    assert view.written_parts == ()


def test_piano_view_preserves_shared_confidence_and_provenance():
    song=ScorebookSongLocator(
        song_id="score.test",
        book_id="scorebook.real.1",
        title="Test",
        start_page=12,
        status=ScoreIngestStatus.STRUCTURED,
        evidence=(
            ScoreEvidence(
                ScoreEvidenceKind.SECTION_ROLE,
                "solo section",
                confidence=.87,
                source_page=12,
                provenance=("vision:page12","manual-verified"),
            ),
            ScoreEvidence(
                ScoreEvidenceKind.WRITTEN_PART,
                "piano figure",
                confidence=.93,
                source_page=12,
                provenance=("vision:page12",),
            ),
        ),
    )
    view=build_piano_scorebook_evidence_view(song)
    assert view.section_roles==("solo section",)
    assert view.written_parts==("piano figure",)
    assert view.evidence_confidence_floor==.87
    assert "vision:page12" in view.provenance
    assert "manual-verified" in view.provenance
    assert "score_page:scorebook.real.1:12" in view.provenance
