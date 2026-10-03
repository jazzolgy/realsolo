from fractions import Fraction

import pytest

from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import ScoreEvent, ScorePart
from music_intelligence.transcribe.spelling import WrittenPitch


def _note(
    event_id,
    voice_id,
    onset,
    duration,
    *,
    group_id=None,
    pitch=("C", 0, 5),
):
    return ScoreEvent(
        event_id=event_id,
        part_id="piano",
        staff_id="upper",
        voice_id=voice_id,
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(onset), Fraction(duration)),
        source_event_ids=(f"src:{event_id}",),
        written_pitch=WrittenPitch(*pitch),
        simultaneity_group_id=group_id,
    )


def test_same_voice_overlapping_notes_are_rejected_without_chord_group():
    part = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("upper",),
        (
            _note("a", "v1", 0, 2),
            _note("b", "v1", 1, 1),
        ),
    )

    with pytest.raises(ValueError, match="overlapping events"):
        part.validate()


def test_overlapping_notes_in_distinct_voices_are_valid():
    part = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("upper",),
        (
            _note("a", "v1", 0, 2),
            _note("b", "v2", 1, 1),
        ),
    )

    part.validate()


def test_simultaneous_chord_members_may_share_one_voice_and_time_span():
    part = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("upper",),
        (
            _note("c", "v1", 0, 1, group_id="chord:1", pitch=("C", 0, 5)),
            _note("e", "v1", 0, 1, group_id="chord:1", pitch=("E", 0, 5)),
            _note("g", "v1", 0, 1, group_id="chord:1", pitch=("G", 0, 5)),
        ),
    )

    part.validate()
