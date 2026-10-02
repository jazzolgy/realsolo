from music_intelligence.corpus.scorebooks import SEED_SONG_LOCATORS
from players.bass.scorebook_study import (
    BassScorebookStudyTrack,
    classify_scorebook_bass_study,
)


def seed(title):
    return next(x for x in SEED_SONG_LOCATORS if x.title == title)


def test_along_came_betty_routes_to_walking_instruction_not_written_part():
    decision = classify_scorebook_bass_study(seed("Along Came Betty").evidence)
    assert decision.track is BassScorebookStudyTrack.WALKING_INSTRUCTION


def test_asa_routes_to_funk_written_part_not_walking():
    decision = classify_scorebook_bass_study(seed("Asa (The Zoo Blues)").evidence)
    assert decision.track is BassScorebookStudyTrack.FUNK_WRITTEN_PART


def test_actual_proof_routes_to_interpretive_funk():
    decision = classify_scorebook_bass_study(seed("Actual Proof").evidence)
    assert decision.track is BassScorebookStudyTrack.INTERPRETIVE_FUNK
