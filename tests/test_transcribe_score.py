from fractions import Fraction

from music_intelligence.transcribe.events import UnpitchedToken
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import (
    ScoreEvent,
    ScorePart,
    assemble_score,
    extract_individual_part,
)
from music_intelligence.transcribe.spelling import WrittenPitch


def pitched_event(event_id, part, staff, voice, onset, midi_name):
    step, alter, octave = midi_name
    return ScoreEvent(
        event_id=event_id,
        part_id=part,
        staff_id=staff,
        voice_id=voice,
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(onset), Fraction(1)),
        source_event_ids=(f"source:{event_id}",),
        written_pitch=WrittenPitch(step, alter, octave),
    )


def test_full_score_and_individual_part_share_same_notation_events():
    piano_event = pitched_event("p1", "piano", "piano:upper", "v1", 0, ("C", 0, 4))
    bass_event = pitched_event("b1", "bass", "bass:staff", "v1", 0, ("C", 0, 2))
    piano = ScorePart("piano", "Piano", "piano", ("piano:upper", "piano:lower"), (piano_event,))
    bass = ScorePart("bass", "Bass", "upright_bass", ("bass:staff",), (bass_event,))

    score = assemble_score(score_id="score:1", title="Test", parts=(piano, bass))
    part = extract_individual_part(score, "piano")

    assert len(score.parts) == 2
    assert len(part.parts) == 1
    assert part.parts[0].events[0] == piano_event


def test_unpitched_score_event_is_valid_without_fake_written_pitch():
    event = ScoreEvent(
        event_id="drum:1",
        part_id="drums",
        staff_id="drums:staff",
        voice_id="drums:snare",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1, 2)),
        source_event_ids=("source:drum:1",),
        unpitched=UnpitchedToken("snare"),
        markings=("ghost",),
    )
    event.validate()
    assert event.written_pitch is None
