from fractions import Fraction
from xml.etree import ElementTree as ET

from music_intelligence.transcribe.engraving import EngravingPlan
from music_intelligence.transcribe.layout import (
    LayoutActionKind,
    grace_spacing_decisions,
    layout_actions,
)
from music_intelligence.transcribe.musicxml import score_to_musicxml
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import (
    GraceNoteKind,
    ScoreEvent,
    ScorePart,
    assemble_score,
)
from music_intelligence.transcribe.spelling import WrittenPitch


def test_grace_note_has_logical_identity_but_reduced_layout_spacing():
    grace = ScoreEvent(
        event_id="grace",
        part_id="sax",
        staff_id="staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1, 8)),
        source_event_ids=("src:g",),
        written_pitch=WrittenPitch("D", 0, 5),
        grace_kind=GraceNoteKind.ACCIACCATURA,
    )
    main = ScoreEvent(
        event_id="main",
        part_id="sax",
        staff_id="staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1)),
        source_event_ids=("src:m",),
        written_pitch=WrittenPitch("E", 0, 5),
    )
    part = ScorePart("sax", "Sax", "tenor_sax", ("staff",), (grace, main))
    score = assemble_score(score_id="grace:1", title="Grace", parts=(part,))
    plan = EngravingPlan(score_id=score.score_id)

    decision = grace_spacing_decisions(score)[0]
    actions = layout_actions(score, plan)

    assert decision.spacing_weight < 1.0
    assert decision.attach_to_following_event_id == "main"
    assert any(a.kind is LayoutActionKind.GRACE_NOTE_RESPACING for a in actions)


def test_acciaccatura_exports_as_slashed_musicxml_grace_without_duration():
    grace = ScoreEvent(
        event_id="g",
        part_id="sax",
        staff_id="staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1, 8)),
        source_event_ids=("src:g",),
        written_pitch=WrittenPitch("D", 0, 5),
        grace_kind=GraceNoteKind.ACCIACCATURA,
    )
    part = ScorePart("sax", "Sax", "tenor_sax", ("staff",), (grace,))
    score = assemble_score(score_id="grace:xml", title="Grace XML", parts=(part,))
    xml = score_to_musicxml(score)
    root = ET.fromstring(xml)
    note = root.find(".//note")

    assert note is not None
    assert note.find("grace").attrib["slash"] == "yes"
    assert note.find("duration") is None
