from fractions import Fraction
from xml.etree import ElementTree as ET

from music_intelligence.transcribe.notation import (
    NotatedAtomKind,
    ScoreSpan,
    TupletRatio,
)
from music_intelligence.transcribe.score import ScoreEvent, ScorePart, assemble_score
from music_intelligence.transcribe.spelling import WrittenPitch
from music_intelligence.transcribe.musicxml import score_to_musicxml


def test_musicxml_exports_full_score_parts_pitch_ties_and_tuplet():
    first = ScoreEvent(
        event_id="p1a",
        part_id="piano",
        staff_id="piano:upper",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(7, 2), Fraction(1, 2)),
        source_event_ids=("src:1",),
        written_pitch=WrittenPitch("C", 1, 4),
        tie_to_next=True,
        tuplet=TupletRatio(3, 2),
        articulations=("accent",),
    )
    second = ScoreEvent(
        event_id="p1b",
        part_id="piano",
        staff_id="piano:upper",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(4), Fraction(1, 2)),
        source_event_ids=("src:1",),
        written_pitch=WrittenPitch("C", 1, 4),
        tie_from_previous=True,
    )
    piano = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("piano:upper", "piano:lower"),
        (first, second),
    )
    score = assemble_score(score_id="s1", title="Readable Result", parts=(piano,))

    xml = score_to_musicxml(score)
    root = ET.fromstring(xml)

    assert root.tag == "score-partwise"
    assert root.findtext("./work/work-title") == "Readable Result"
    assert root.find("./part-list/score-part[@id='piano']") is not None
    assert len(root.findall("./part[@id='piano']/measure")) == 2
    assert root.find(".//pitch/step").text == "C"
    assert root.find(".//pitch/alter").text == "1"
    assert root.find(".//time-modification/actual-notes").text == "3"
    assert root.find(".//tie[@type='start']") is not None
    assert root.find(".//tie[@type='stop']") is not None


def test_musicxml_is_projection_not_score_model_mutation():
    event = ScoreEvent(
        event_id="sax:1",
        part_id="sax",
        staff_id="sax:staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1)),
        source_event_ids=("performed:sax:1",),
        written_pitch=WrittenPitch("B", -1, 4),
        markings=("scoop",),
    )
    part = ScorePart("sax", "Tenor Sax", "tenor_sax", ("sax:staff",), (event,))
    score = assemble_score(score_id="s2", title="Part", parts=(part,))
    before = score.parts[0].events[0]

    xml = score_to_musicxml(score)

    assert "scoop" in xml
    assert score.parts[0].events[0] == before
