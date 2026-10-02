from fractions import Fraction

from music_intelligence.transcribe.engraving import (
    EngravingIntent,
    EngravingPlan,
)
from music_intelligence.transcribe.layout import (\n    LayoutActionKind,\n    layout_actions,\n    optical_spacing_decisions,\n)
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan, TupletRatio
from music_intelligence.transcribe.score import ScoreEvent, ScorePart, assemble_score
from music_intelligence.transcribe.spelling import WrittenPitch


def test_optical_spacing_pressure_is_separate_from_note_duration():
    event = ScoreEvent(
        event_id="n:1",
        part_id="piano",
        staff_id="upper",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1, 2)),
        source_event_ids=("src:1",),
        written_pitch=WrittenPitch("C", 1, 5),
        articulations=("accent",),
        tuplet=TupletRatio(3, 2),
    )
    part = ScorePart("piano", "Piano", "piano", ("upper", "lower"), (event,))
    score = assemble_score(score_id="layout:1", title="Layout", parts=(part,))
    plan = EngravingPlan(
        score_id=score.score_id,
        intents=(
            EngravingIntent(
                "n:1",
                horizontal_spacing_weight=1.0,
                cross_staff_target="lower",
            ),
        ),
    )

    decision = optical_spacing_decisions(score, plan)[0]

    assert decision.spacing_weight > 1.0
    assert event.span.duration == Fraction(1, 2)
    assert "accidental needs horizontal clearance" in decision.reasons
    assert "cross-staff notation may need horizontal clearance" in decision.reasons


def test_simultaneous_voices_create_layout_pressure_without_changing_voice_ids():
    upper = ScoreEvent(
        event_id="u",
        part_id="piano",
        staff_id="upper",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1)),
        source_event_ids=("src:u",),
        written_pitch=WrittenPitch("G", 0, 5),
    )
    lower = ScoreEvent(
        event_id="l",
        part_id="piano",
        staff_id="upper",
        voice_id="v2",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1)),
        source_event_ids=("src:l",),
        written_pitch=WrittenPitch("C", 0, 4),
    )
    part = ScorePart("piano", "Piano", "piano", ("upper", "lower"), (upper, lower))
    score = assemble_score(score_id="layout:2", title="Voices", parts=(part,))
    plan = EngravingPlan(score_id=score.score_id)

    decisions = {d.event_id: d for d in optical_spacing_decisions(score, plan)}

    assert decisions["u"].spacing_weight > 1.0
    assert decisions["l"].spacing_weight > 1.0
    assert upper.voice_id == "v1"
    assert lower.voice_id == "v2"



def test_magnetic_layout_repositions_attached_objects_without_changing_note_spacing_semantics():
    event = ScoreEvent(
        event_id="mag:1",
        part_id="sax",
        staff_id="sax:staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1)),
        source_event_ids=("src:mag",),
        written_pitch=WrittenPitch("F", 0, 4),
        articulations=("accent", "staccato"),
        markings=("scoop",),
    )
    part = ScorePart("sax", "Tenor Sax", "tenor_sax", ("sax:staff",), (event,))
    score = assemble_score(score_id="layout:mag", title="Magnetic", parts=(part,))
    plan = EngravingPlan(score_id=score.score_id)

    actions = layout_actions(score, plan)

    assert any(a.kind is LayoutActionKind.MAGNETIC_REPOSITION for a in actions)
    assert not any(a.kind is LayoutActionKind.HORIZONTAL_RESPACING for a in actions)
    assert event.span.duration == Fraction(1)



def test_auto_respace_off_preserves_horizontal_spacing_even_when_pressure_exists():
    event = ScoreEvent(
        event_id="space:off",
        part_id="piano",
        staff_id="upper",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1, 2)),
        source_event_ids=("src:space",),
        written_pitch=WrittenPitch("C", 1, 5),
    )
    part = ScorePart("piano", "Piano", "piano", ("upper",), (event,))
    score = assemble_score(score_id="layout:off", title="No Respace", parts=(part,))

    from music_intelligence.transcribe.engraving import EngravingProfile
    plan = EngravingPlan(
        score_id=score.score_id,
        profile=EngravingProfile(auto_respace=False),
    )

    actions = layout_actions(score, plan)
    decision = optical_spacing_decisions(score, plan)[0]

    assert not any(a.kind is LayoutActionKind.HORIZONTAL_RESPACING for a in actions)
    assert decision.spacing_weight == 1.0
