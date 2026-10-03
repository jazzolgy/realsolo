import pytest

from music_intelligence.learning.note_evidence import (
    NoteEvidenceStatus,
    NoteLevelEvidence,
    may_promote_as_legend_note,
)
from music_intelligence.learning.score_alignment import MusicalScoreCoordinate


def coord():
    return MusicalScoreCoordinate(
        song_id="Autumn Leaves",
        score_source_id="realchord:96",
        realchord_id="96",
        section="A1",
        bar=1,
        beat=1.0,
        form_length_bars=32,
        form_bar=1,
    )


def test_mixed_audio_pitch_hypothesis_is_not_exact_transcription():
    e=NoteLevelEvidence(
        evidence_id="x",
        pitch_midi=60.0,
        onset_sec=716.0,
        status=NoteEvidenceStatus.NOTE_HYPOTHESIS,
        pitch_confidence=.8,
        onset_confidence=.8,
    )
    e.validate()
    assert not e.is_exact_transcription
    assert not may_promote_as_legend_note(e)


def test_ground_truth_requires_instrument_coordinate_and_high_verification():
    with pytest.raises(ValueError):
        NoteLevelEvidence(
            evidence_id="bad",
            pitch_midi=64,
            coordinate=coord(),
            instrument="piano",
            status=NoteEvidenceStatus.GROUND_TRUTH_TRANSCRIPTION,
            verification_confidence=.7,
        ).validate()


def test_verified_piano_note_can_be_promoted():
    e=NoteLevelEvidence(
        evidence_id="ok",
        pitch_midi=64,
        coordinate=coord(),
        onset_sec=716.1,
        instrument="piano",
        voice="RH",
        status=NoteEvidenceStatus.EXPERT_VERIFIED,
        pitch_confidence=.98,
        onset_confidence=.97,
        attribution_confidence=.97,
        verification_confidence=.96,
    )
    assert may_promote_as_legend_note(e)
