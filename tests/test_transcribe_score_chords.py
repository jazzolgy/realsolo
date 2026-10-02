from fractions import Fraction
import pytest

from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import ScoreEvent, ScorePart
from music_intelligence.transcribe.spelling import WrittenPitch


def note(event_id, midi_step, onset, duration, group=None):
    return ScoreEvent(
        event_id=event_id,
        part_id="piano",
        staff_id="upper",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(onset), Fraction(duration)),
        source_event_ids=(f"src:{event_id}",),
        written_pitch=WrittenPitch(midi_step, 0, 4),
        simultaneity_group_id=group,
    )


def test_simultaneity_group_requires_matching_span_and_voice():
    part = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("upper",),
        (
            note("c", "C", 0, 1, "chord:1"),
            note("e", "E", 0, 1, "chord:1"),
            note("g", "G", 0, 1, "chord:1"),
        ),
    )

    part.validate()


def test_simultaneity_group_rejects_different_duration():
    part = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("upper",),
        (
            note("c", "C", 0, 1, "chord:1"),
            note("e", "E", 0, 2, "chord:1"),
        ),
    )

    with pytest.raises(ValueError, match="share part/staff/voice/onset/duration"):
        part.validate()


def test_single_note_may_not_claim_a_chord_group():
    part = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("upper",),
        (note("c", "C", 0, 1, "chord:solo"),),
    )

    with pytest.raises(ValueError, match="requires at least two notes"):
        part.validate()
