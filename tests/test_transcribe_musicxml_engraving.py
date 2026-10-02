from fractions import Fraction
from xml.etree import ElementTree as ET

from music_intelligence.transcribe.engraving import (
    BeamState,
    EngravingIntent,
    EngravingPlan,
    StemDirection,
)
from music_intelligence.transcribe.musicxml import score_to_musicxml
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import ScoreEvent, ScorePart, assemble_score
from music_intelligence.transcribe.spelling import WrittenPitch


def _score():
    events = (
        ScoreEvent(
            event_id="p:1",
            part_id="piano",
            staff_id="piano:upper",
            voice_id="v1",
            kind=NotatedAtomKind.NOTE,
            span=ScoreSpan(Fraction(0), Fraction(1, 2)),
            source_event_ids=("src:1",),
            written_pitch=WrittenPitch("C", 0, 5),
        ),
        ScoreEvent(
            event_id="p:2",
            part_id="piano",
            staff_id="piano:upper",
            voice_id="v1",
            kind=NotatedAtomKind.NOTE,
            span=ScoreSpan(Fraction(1, 2), Fraction(1, 2)),
            source_event_ids=("src:2",),
            written_pitch=WrittenPitch("D", 0, 5),
        ),
    )
    part = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("piano:upper", "piano:lower"),
        events,
    )
    return assemble_score(score_id="s:engraving", title="Engraving XML", parts=(part,))


def test_musicxml_can_project_stem_and_beam_without_mutating_logical_score():
    score = _score()
    before = score.parts[0].events
    plan = EngravingPlan(
        score_id=score.score_id,
        intents=(
            EngravingIntent(
                "p:1",
                stem_direction=StemDirection.UP,
                beam_state=BeamState.BEGIN,
                beam_group_id="beam:1",
            ),
            EngravingIntent(
                "p:2",
                stem_direction=StemDirection.UP,
                beam_state=BeamState.END,
                beam_group_id="beam:1",
            ),
        ),
    )

    xml = score_to_musicxml(score, plan)
    root = ET.fromstring(xml)
    notes = root.findall(".//note")

    assert notes[0].findtext("stem") == "up"
    assert notes[0].findtext("beam") == "begin"
    assert notes[1].findtext("beam") == "end"
    assert score.parts[0].events == before


def test_cross_staff_is_visual_projection_not_logical_staff_rewrite():
    score = _score()
    plan = EngravingPlan(
        score_id=score.score_id,
        intents=(
            EngravingIntent(
                "p:1",
                cross_staff_target="piano:lower",
            ),
            EngravingIntent("p:2"),
        ),
    )

    xml = score_to_musicxml(score, plan)
    root = ET.fromstring(xml)
    notes = root.findall(".//note")

    assert notes[0].findtext("staff") == "2"
    assert notes[1].findtext("staff") == "1"
    assert score.parts[0].events[0].staff_id == "piano:upper"
