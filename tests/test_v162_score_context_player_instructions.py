from music_intelligence.corpus import (
    SEED_SONG_LOCATORS,
    ScorePosition,
    resolve_score_context,
)


def song(title):
    return next(x for x in SEED_SONG_LOCATORS if x.title == title)


def test_betty_score_context_exposes_bass_walk_instruction():
    snap = resolve_score_context(
        song("Along Came Betty"),
        ScorePosition(page=8),
    )
    assert ("bass", "bass walks") in snap.player_instructions
    assert snap.written_part_role is None


def test_actual_proof_score_context_preserves_interpretive_written_part_policy():
    snap = resolve_score_context(
        song("Actual Proof"),
        ScorePosition(page=2),
    )
    assert snap.written_part_role == "dedicated bass page"
    assert "freely interpreted" in (snap.written_part_policy or "")
    assert "last two bars of A" in (snap.written_part_policy or "")


def test_asa_score_context_marks_written_part_without_inventing_walking_instruction():
    snap = resolve_score_context(
        song("Asa (The Zoo Blues)"),
        ScorePosition(page=10),
    )
    assert "syncopated funk bass" in (snap.written_part_role or "")
    assert not snap.player_instructions
