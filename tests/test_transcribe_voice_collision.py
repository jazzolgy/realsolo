from fractions import Fraction

from music_intelligence.transcribe.engraving import build_default_engraving_plan
from music_intelligence.transcribe.layout import (
    HorizontalSide,
    accidental_columns,
    notehead_displacements,
)
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import ScoreEvent, ScorePart, assemble_score
from music_intelligence.transcribe.spelling import WrittenPitch


def note(eid, voice, pitch):
    return ScoreEvent(
        event_id=eid,
        part_id="piano",
        staff_id="upper",
        voice_id=voice,
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1)),
        source_event_ids=("src:" + eid,),
        written_pitch=pitch,
    )


def test_unison_in_opposing_voices_gets_horizontal_notehead_displacement():
    upper = note("upper", "v1", WrittenPitch("C", 0, 5))
    lower = note("lower", "v2", WrittenPitch("C", 0, 5))
    part = ScorePart("piano", "Piano", "piano", ("upper",), (upper, lower))
    score = assemble_score(score_id="collision:1", title="Collision", parts=(part,))
    plan = build_default_engraving_plan(score)

    decisions = {d.event_id: d.side for d in notehead_displacements(score, plan)}

    assert decisions["upper"] is HorizontalSide.RIGHT
    assert decisions["lower"] is HorizontalSide.LEFT
    assert upper.voice_id == "v1"
    assert lower.voice_id == "v2"


def test_adjacent_accidentals_can_be_packed_into_multiple_columns():
    first = note("a", "v1", WrittenPitch("F", 1, 5))
    second = note("b", "v2", WrittenPitch("G", -1, 5))
    part = ScorePart("piano", "Piano", "piano", ("upper",), (first, second))
    score = assemble_score(score_id="acc:1", title="Accidentals", parts=(part,))

    columns = {d.event_id: d.column for d in accidental_columns(score)}

    assert set(columns) == {"a", "b"}
    assert len(set(columns.values())) == 2
