from music_intelligence.corpus import (
    SEED_SONG_LOCATORS,
    ScoreContextSnapshot,
    ScoreEvidenceKind,
    ScorePosition,
    ScoreSpan,
    StructuredScoreEvidence,
    resolve_score_context,
)


def _song(title: str):
    return next(x for x in SEED_SONG_LOCATORS if x.title == title)


def test_page_level_style_is_resolved_without_inventing_bar_context():
    snap = resolve_score_context(_song("Anthropology"), ScorePosition(page=11))
    assert snap.style == ("fast bebop",)
    assert snap.section is None
    assert snap.current_feel is None
    assert snap.solo_indication is None


def test_page_level_feel_change_is_not_promoted_to_current_or_pending_state():
    snap = resolve_score_context(_song("Alfie's Theme"), ScorePosition(page=4, bar=1))
    assert snap.current_feel is None
    assert snap.feel_change_here is None
    assert snap.pending_feel_change is None
    assert len(snap.unresolved_evidence) == 3
    assert all(x.kind is ScoreEvidenceKind.FEEL_CHANGE for x in snap.unresolved_evidence)


def test_precisely_located_feel_change_can_be_pending_then_current_event():
    loc = _song("Anthropology")
    ev = (
        StructuredScoreEvidence(
            ScoreEvidenceKind.FEEL,
            "two feel",
            ScoreSpan(page=11, start_bar=1, end_bar=8),
            .99,
            ("manual:bar-map",),
        ),
        StructuredScoreEvidence(
            ScoreEvidenceKind.FEEL_CHANGE,
            "in four",
            ScoreSpan(page=11, start_bar=9),
            .99,
            ("manual:bar-map",),
        ),
    )
    before = resolve_score_context(loc, ScorePosition(page=11, bar=8), ev)
    at = resolve_score_context(loc, ScorePosition(page=11, bar=9), ev)
    assert before.current_feel == "two feel"
    assert before.pending_feel_change == "in four"
    assert at.feel_change_here == "in four"


def test_section_phrase_boundary_written_melody_and_solo_are_explicit_only():
    loc = _song("Anthropology")
    ev = (
        StructuredScoreEvidence(
            ScoreEvidenceKind.SECTION,
            "B",
            ScoreSpan(page=11, start_bar=9, end_bar=16),
            .98,
        ),
        StructuredScoreEvidence(
            ScoreEvidenceKind.PHRASE_BOUNDARY,
            "after",
            ScoreSpan(page=11, start_bar=12, start_beat=4.0, end_bar=12, end_beat=4.0),
            .95,
        ),
        StructuredScoreEvidence(
            ScoreEvidenceKind.WRITTEN_MELODY,
            "head melody",
            ScoreSpan(page=11, start_bar=9, end_bar=16),
            .99,
        ),
        StructuredScoreEvidence(
            ScoreEvidenceKind.SOLO_INDICATION,
            "open solo",
            ScoreSpan(page=11, start_bar=17, end_bar=32),
            .99,
        ),
    )
    head = resolve_score_context(loc, ScorePosition(page=11, bar=12, beat=4.0), ev)
    solo = resolve_score_context(loc, ScorePosition(page=11, bar=20), ev)
    assert head.section == "B"
    assert head.phrase_boundary_after
    assert head.written_melody_active
    assert head.written_part_role == "head melody"
    assert head.solo_indication is None
    assert solo.solo_indication == "open solo"
    assert not solo.written_melody_active


def test_snapshot_preserves_shared_book_song_page_identity():
    loc = _song("Autumn Leaves")
    snap = resolve_score_context(loc, ScorePosition(page=12))
    assert isinstance(snap, ScoreContextSnapshot)
    assert snap.book_id == "scorebook.newreal.1"
    assert snap.song_id == "score.newreal1.autumn_leaves"
    assert snap.position.page == 12
