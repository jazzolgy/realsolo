from fractions import Fraction

from music_intelligence.transcribe.engraving import (
    BeamState,
    EngravingPlan,
    EngravingProfile,
    StemDirection,
    VerticalPlacement,
    beam_group_intents,
    build_default_engraving_plan,
    cross_staff_primary_beam_side,
    cross_staff_tie_placement,
    tuplet_group_placement,
)
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan, TupletRatio
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


def test_four_four_eighths_beam_in_fours_by_default():
    score = score_with(
        (
            event("a", "voice1", Fraction(0)),
            event("b", "voice1", Fraction(1, 2)),
            event("c", "voice1", Fraction(1)),
            event("d", "voice1", Fraction(3, 2)),
        )
    )
    plan = build_default_engraving_plan(score)
    by_id = {i.event_id: i for i in plan.intents}

    assert by_id["a"].beam_state is BeamState.BEGIN
    assert by_id["b"].beam_state is BeamState.CONTINUE
    assert by_id["c"].beam_state is BeamState.CONTINUE
    assert by_id["d"].beam_state is BeamState.END
    assert len({by_id[x].beam_group_id for x in ("a", "b", "c", "d")}) == 1


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



def test_beam_group_breaks_when_written_rhythm_changes():
    events = (
        event("r1", "voice1", Fraction(0), Fraction(1, 2)),
        event("r2", "voice1", Fraction(1, 2), Fraction(1, 4)),
        event("r3", "voice1", Fraction(3, 4), Fraction(1, 4)),
        event("r4", "voice1", Fraction(1), Fraction(1, 2)),
    )
    result = beam_group_intents(events, beat_group=Fraction(2))

    assert result["r1"] == (BeamState.NONE, None)
    assert result["r2"][0] is BeamState.BEGIN
    assert result["r3"][0] is BeamState.END
    assert result["r4"] == (BeamState.NONE, None)


def test_tuplet_position_can_use_whole_group_instead_of_first_note_only():
    ratio = TupletRatio(3, 2)
    low_first = ScoreEvent(
        event_id="t1",
        part_id="piano",
        staff_id="piano:upper",
        voice_id="voice1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1, 3)),
        source_event_ids=("src:t1",),
        written_pitch=WrittenPitch("C", 0, 4),
        tuplet=ratio,
    )
    high_second = ScoreEvent(
        event_id="t2",
        part_id="piano",
        staff_id="piano:upper",
        voice_id="voice1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(1, 3), Fraction(1, 3)),
        source_event_ids=("src:t2",),
        written_pitch=WrittenPitch("C", 0, 6),
        tuplet=ratio,
    )
    high_third = ScoreEvent(
        event_id="t3",
        part_id="piano",
        staff_id="piano:upper",
        voice_id="voice1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(2, 3), Fraction(1, 3)),
        source_event_ids=("src:t3",),
        written_pitch=WrittenPitch("G", 0, 5),
        tuplet=ratio,
    )

    group_based = tuplet_group_placement(
        (low_first, high_second, high_third),
        position_as_if_all_notes_beamed=True,
    )
    first_note_based = tuplet_group_placement(
        (low_first, high_second, high_third),
        position_as_if_all_notes_beamed=False,
    )

    assert group_based["t1"] is VerticalPlacement.BELOW
    assert first_note_based["t1"] is VerticalPlacement.ABOVE
    assert group_based["t1"] == group_based["t2"] == group_based["t3"]


def test_tuplet_can_be_separated_from_adjacent_notes_by_profile():
    normal = event("n", "voice1", Fraction(0), Fraction(1, 2))
    triplet = ScoreEvent(
        event_id="trip",
        part_id="piano",
        staff_id="piano:upper",
        voice_id="voice1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(1, 2), Fraction(1, 2)),
        source_event_ids=("src:trip",),
        written_pitch=WrittenPitch("D", 0, 4),
        tuplet=TupletRatio(3, 2),
    )

    joined = beam_group_intents(
        (normal, triplet),
        beat_group=Fraction(2),
        separate_tuplets_from_adjacent_notes=False,
    )
    separated = beam_group_intents(
        (normal, triplet),
        beat_group=Fraction(2),
        separate_tuplets_from_adjacent_notes=True,
    )

    assert joined["n"][0] is BeamState.BEGIN
    assert joined["trip"][0] is BeamState.END
    assert separated["n"] == (BeamState.NONE, None)
    assert separated["trip"] == (BeamState.NONE, None)



def test_cross_staff_tie_can_reuse_normal_tie_position_rules():
    tied = ScoreEvent(
        event_id="tie:1",
        part_id="piano",
        staff_id="piano:upper",
        voice_id="voice1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1)),
        source_event_ids=("src:tie",),
        written_pitch=WrittenPitch("C", 0, 5),
        tie_to_next=True,
    )
    intent = __import__(
        "music_intelligence.transcribe.engraving",
        fromlist=["EngravingIntent"],
    ).EngravingIntent(
        "tie:1",
        stem_direction=StemDirection.UP,
        cross_staff_target="piano:lower",
    )

    placement = cross_staff_tie_placement(
        tied,
        intent,
        EngravingProfile(apply_tie_rules_to_cross_staff=True),
    )
    legacy = cross_staff_tie_placement(
        tied,
        intent,
        EngravingProfile(apply_tie_rules_to_cross_staff=False),
    )

    assert placement is VerticalPlacement.BELOW
    assert legacy is VerticalPlacement.AUTO



def test_cross_staff_primary_beam_can_follow_first_note_side_rule():
    first = event("beam:first", "voice1", Fraction(0))
    second = event("beam:second", "voice1", Fraction(1, 2))
    EngravingIntent = __import__(
        "music_intelligence.transcribe.engraving",
        fromlist=["EngravingIntent"],
    ).EngravingIntent
    intents = (
        EngravingIntent("beam:first"),
        EngravingIntent("beam:second", cross_staff_target="piano:lower"),
    )

    side = cross_staff_primary_beam_side(
        (first, second),
        intents,
        EngravingProfile(avoid_cross_staff_beam_corners=True),
    )
    legacy = cross_staff_primary_beam_side(
        (first, second),
        intents,
        EngravingProfile(avoid_cross_staff_beam_corners=False),
    )

    assert side.value == "first_note"
    assert legacy.value == "auto"



def test_four_four_eighths_form_two_groups_of_four_across_full_bar():
    events = tuple(
        event(f"e{i}", "voice1", Fraction(i, 2))
        for i in range(8)
    )
    score = score_with(events)
    plan = build_default_engraving_plan(score)
    by_id = {intent.event_id: intent for intent in plan.intents}

    first = [by_id[f"e{i}"].beam_state for i in range(4)]
    second = [by_id[f"e{i}"].beam_state for i in range(4, 8)]
    assert first == [
        BeamState.BEGIN,
        BeamState.CONTINUE,
        BeamState.CONTINUE,
        BeamState.END,
    ]
    assert second == [
        BeamState.BEGIN,
        BeamState.CONTINUE,
        BeamState.CONTINUE,
        BeamState.END,
    ]
    assert by_id["e0"].beam_group_id != by_id["e4"].beam_group_id


def test_twelve_eight_repeats_three_eighth_compound_beam_groups():
    events = tuple(
        event(f"c{i}", "voice1", Fraction(i, 2))
        for i in range(12)
    )
    part = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("piano:upper", "piano:lower"),
        events,
    )
    score = assemble_score(
        score_id="engrave:128",
        title="Twelve Eight",
        parts=(part,),
        meter_numerator=12,
        meter_denominator=8,
    )
    plan = build_default_engraving_plan(score)
    by_id = {intent.event_id: intent for intent in plan.intents}

    for start in (0, 3, 6, 9):
        ids = [f"c{i}" for i in range(start, start + 3)]
        assert [by_id[eid].beam_state for eid in ids] == [
            BeamState.BEGIN,
            BeamState.CONTINUE,
            BeamState.END,
        ]
        assert len({by_id[eid].beam_group_id for eid in ids}) == 1

    assert len({
        by_id["c0"].beam_group_id,
        by_id["c3"].beam_group_id,
        by_id["c6"].beam_group_id,
        by_id["c9"].beam_group_id,
    }) == 4


def test_short_rest_is_never_assigned_a_beam_state():
    rest = ScoreEvent(
        event_id="rest:eighth",
        part_id="piano",
        staff_id="piano:upper",
        voice_id="voice1",
        kind=NotatedAtomKind.REST,
        span=ScoreSpan(Fraction(1, 2), Fraction(1, 2)),
    )
    events = (
        event("before", "voice1", Fraction(0)),
        rest,
        event("after", "voice1", Fraction(1)),
    )

    result = beam_group_intents(events, beat_group=Fraction(2))

    assert result["rest:eighth"] == (BeamState.NONE, None)
    assert result["before"] == (BeamState.NONE, None)
    assert result["after"] == (BeamState.NONE, None)
