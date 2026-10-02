from fractions import Fraction

from music_intelligence.transcribe.engraving import (
    BeamState,
    EngravingPlan,
    EngravingProfile,
    StemDirection,
    build_default_engraving_plan,
)
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import ScoreEvent, ScorePart, assemble_score
from music_intelligence.transcribe.spelling import WrittenPitch


def event(eid, voice, onset, duration=Fraction(1, 2), pitch=("C", 0, 4)):
    return ScoreEvent(
        event_id=eid,
        part_id="piano",
        staff_id="piano:upper",
        voice_id=voice,
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(onset), Fraction(duration)),
        source_event_ids=("src:" + eid,),
        written_pitch=WrittenPitch(*pitch),
    )


def score_with(events):
    part = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("piano:upper", "piano:lower"),
        tuple(events),
    )
    return assemble_score(score_id="engrave:1", title="Engraving", parts=(part,))


def test_logical_score_does_not_contain_stem_or_optical_geometry():
    logical = event("n1", "voice1", 0)
    assert not hasattr(logical, "stem_direction")
    assert not hasattr(logical, "beam_state")
    assert not hasattr(logical, "horizontal_spacing_weight")


def test_simultaneous_independent_voices_receive_opposing_stem_intents():
    score = score_with(
        (
            event("upper", "voice1", 0, pitch=("G", 0, 5)),
            event("lower", "voice2", 0, pitch=("C", 0, 4)),
        )
    )
    plan = build_default_engraving_plan(score)
    directions = {i.event_id: i.stem_direction for i in plan.intents}

    assert directions["upper"] is StemDirection.UP
    assert directions["lower"] is StemDirection.DOWN


def test_short_notes_beam_by_score_beat_not_performance_microtiming():
    score = score_with(
        (
            event("a", "voice1", Fraction(0)),
            event("b", "voice1", Fraction(1, 2)),
            event("c", "voice1", Fraction(1)),
        )
    )
    plan = build_default_engraving_plan(score)
    by_id = {i.event_id: i for i in plan.intents}

    assert by_id["a"].beam_state is BeamState.BEGIN
    assert by_id["b"].beam_state is BeamState.END
    assert by_id["a"].beam_group_id == by_id["b"].beam_group_id
    assert by_id["c"].beam_state is BeamState.NONE


def test_same_logical_score_can_have_different_engraving_profiles():
    score = score_with((event("n1", "voice1", 0),))
    optical = build_default_engraving_plan(
        score,
        profile=EngravingProfile(optical_note_spacing=True),
    )
    mechanical = build_default_engraving_plan(
        score,
        profile=EngravingProfile(optical_note_spacing=False),
    )

    assert optical.profile != mechanical.profile
    assert score.parts[0].events[0] == score.parts[0].events[0]


def test_engraving_plan_rejects_unknown_logical_event():
    score = score_with((event("n1", "voice1", 0),))
    bad = EngravingPlan(
        score_id=score.score_id,
        intents=(),
    )
    bad.validate(score)


def test_compound_meter_beams_eighths_in_dotted_quarter_groups():
    part = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("piano:upper", "piano:lower"),
        (
            event("a68", "voice1", Fraction(0)),
            event("b68", "voice1", Fraction(1, 2)),
            event("c68", "voice1", Fraction(1)),
            event("d68", "voice1", Fraction(3, 2)),
        ),
    )
    score = assemble_score(
        score_id="engrave:68",
        title="Six Eight",
        parts=(part,),
        meter_numerator=6,
        meter_denominator=8,
    )
    plan = build_default_engraving_plan(score)
    by_id = {i.event_id: i for i in plan.intents}

    assert by_id["a68"].beam_state is BeamState.BEGIN
    assert by_id["b68"].beam_state is BeamState.CONTINUE
    assert by_id["c68"].beam_state is BeamState.END
    assert by_id["a68"].beam_group_id == by_id["c68"].beam_group_id
    assert by_id["d68"].beam_state is BeamState.NONE
