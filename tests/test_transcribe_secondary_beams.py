from fractions import Fraction

from music_intelligence.transcribe.engraving import (
    BeamState,
    build_default_engraving_plan,
)
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import ScoreEvent, ScorePart, assemble_score
from music_intelligence.transcribe.spelling import WrittenPitch


def sixteenth(eid, onset):
    return ScoreEvent(
        event_id=eid,
        part_id="piano",
        staff_id="upper",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(onset), Fraction(1, 4)),
        source_event_ids=("src:" + eid,),
        written_pitch=WrittenPitch("C", 0, 5),
    )


def test_secondary_beams_split_simple_meter_at_quarter_subgroups():
    part = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("upper",),
        (
            sixteenth("a", 0),
            sixteenth("b", Fraction(1, 4)),
            sixteenth("c", Fraction(1, 2)),
            sixteenth("d", Fraction(3, 4)),
            sixteenth("e", 1),
            sixteenth("f", Fraction(5, 4)),
        ),
    )
    score = assemble_score(score_id="beam2:44", title="Secondary", parts=(part,))
    plan = build_default_engraving_plan(score)
    by_id = {i.event_id: i for i in plan.intents}

    assert by_id["a"].secondary_beam_state is BeamState.BEGIN
    assert by_id["d"].secondary_beam_state is BeamState.END
    assert by_id["a"].secondary_beam_group_id == by_id["d"].secondary_beam_group_id
    assert by_id["e"].secondary_beam_state is BeamState.BEGIN
    assert by_id["f"].secondary_beam_state is BeamState.END
    assert by_id["e"].secondary_beam_group_id != by_id["a"].secondary_beam_group_id


def test_secondary_beams_use_dotted_quarter_subgroups_in_compound_meter():
    events = tuple(sixteenth(f"n{i}", Fraction(i, 4)) for i in range(6))
    part = ScorePart("piano", "Piano", "piano", ("upper",), events)
    score = assemble_score(
        score_id="beam2:68",
        title="Secondary 6/8",
        parts=(part,),
        meter_numerator=6,
        meter_denominator=8,
    )
    plan = build_default_engraving_plan(score)
    ids = {i.event_id: i.secondary_beam_group_id for i in plan.intents}

    assert len({ids[f"n{i}"] for i in range(6)}) == 1
