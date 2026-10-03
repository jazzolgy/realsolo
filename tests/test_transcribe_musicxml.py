from fractions import Fraction
from xml.etree import ElementTree as ET

from music_intelligence.transcribe.notation import (
    NotatedAtomKind,
    ScoreSpan,
    TupletRatio,
)
from music_intelligence.transcribe.score import ScoreEvent, ScoreKeySignature, ScorePart, assemble_score
from music_intelligence.transcribe.spelling import WrittenPitch
from music_intelligence.transcribe.engraving import build_default_engraving_plan
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



def test_musicxml_emits_written_key_for_bb_transposing_part():
    event = ScoreEvent(
        event_id="cl:1",
        part_id="clarinet",
        staff_id="clarinet:staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1)),
        source_event_ids=("src:cl:1",),
        written_pitch=WrittenPitch("D", 0, 4),
    )
    part = ScorePart(
        "clarinet",
        "Clarinet in Bb",
        "clarinet_bb",
        ("clarinet:staff",),
        (event,),
    )
    score = assemble_score(
        score_id="key:bb",
        title="Concert C",
        parts=(part,),
        key_signature=ScoreKeySignature(0, "major"),
    )

    root = ET.fromstring(score_to_musicxml(score))

    assert root.findtext(".//attributes/key/fifths") == "2"
    assert root.findtext(".//attributes/key/mode") == "major"
    assert root.findtext(".//attributes/transpose/chromatic") == "-2"


def test_musicxml_emits_concert_key_for_non_transposing_part():
    event = ScoreEvent(
        event_id="fl:1",
        part_id="flute",
        staff_id="flute:staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1)),
        source_event_ids=("src:fl:1",),
        written_pitch=WrittenPitch("B", -1, 4),
    )
    part = ScorePart("flute", "Flute", "flute", ("flute:staff",), (event,))
    score = assemble_score(
        score_id="key:flute",
        title="Concert F",
        parts=(part,),
        key_signature=ScoreKeySignature(-1, "major"),
    )

    root = ET.fromstring(score_to_musicxml(score))

    assert root.findtext(".//attributes/key/fifths") == "-1"



def test_musicxml_emits_explicit_dotted_note_type():
    event = ScoreEvent(
        event_id="dot:1",
        part_id="flute",
        staff_id="flute:staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(3, 2)),
        source_event_ids=("src:dot:1",),
        written_pitch=WrittenPitch("C", 0, 5),
    )
    part = ScorePart("flute", "Flute", "flute", ("flute:staff",), (event,))
    score = assemble_score(score_id="dot:score", title="Dotted", parts=(part,))

    root = ET.fromstring(score_to_musicxml(score))
    note = root.find(".//part[@id='flute']/measure/note")

    assert note.findtext("type") == "quarter"
    assert note.find("dot") is not None


def test_musicxml_triplet_duration_keeps_written_eighth_type():
    event = ScoreEvent(
        event_id="triplet:1",
        part_id="flute",
        staff_id="flute:staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1, 3)),
        source_event_ids=("src:triplet:1",),
        written_pitch=WrittenPitch("D", 0, 5),
        tuplet=TupletRatio(3, 2),
    )
    part = ScorePart("flute", "Flute", "flute", ("flute:staff",), (event,))
    score = assemble_score(score_id="triplet:score", title="Triplet", parts=(part,))

    root = ET.fromstring(score_to_musicxml(score))
    note = root.find(".//part[@id='flute']/measure/note")

    assert note.findtext("type") == "eighth"
    assert note.findtext("time-modification/actual-notes") == "3"
    assert note.findtext("time-modification/normal-notes") == "2"



def test_musicxml_emits_compound_meter_beams_in_three_eighth_groups():
    events = tuple(
        ScoreEvent(
            event_id=f"e{i}",
            part_id="flute",
            staff_id="flute:staff",
            voice_id="v1",
            kind=NotatedAtomKind.NOTE,
            span=ScoreSpan(Fraction(i, 2), Fraction(1, 2)),
            source_event_ids=(f"src:e{i}",),
            written_pitch=WrittenPitch("C", 0, 5),
        )
        for i in range(6)
    )
    part = ScorePart("flute", "Flute", "flute", ("flute:staff",), events)
    score = assemble_score(
        score_id="beam:68",
        title="Compound Beams",
        parts=(part,),
        meter_numerator=6,
        meter_denominator=8,
    )

    root = ET.fromstring(
        score_to_musicxml(score, build_default_engraving_plan(score))
    )
    beam_values = [
        note.findtext("beam[@number='1']")
        for note in root.findall(".//part[@id='flute']/measure/note")
    ]

    assert beam_values == [
        "begin",
        "continue",
        "end",
        "begin",
        "continue",
        "end",
    ]


def test_musicxml_does_not_emit_beam_on_short_rest():
    note1 = ScoreEvent(
        event_id="n1",
        part_id="flute",
        staff_id="flute:staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1, 2)),
        source_event_ids=("src:n1",),
        written_pitch=WrittenPitch("C", 0, 5),
    )
    rest = ScoreEvent(
        event_id="r1",
        part_id="flute",
        staff_id="flute:staff",
        voice_id="v1",
        kind=NotatedAtomKind.REST,
        span=ScoreSpan(Fraction(1, 2), Fraction(1, 2)),
    )
    note2 = ScoreEvent(
        event_id="n2",
        part_id="flute",
        staff_id="flute:staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(1), Fraction(1, 2)),
        source_event_ids=("src:n2",),
        written_pitch=WrittenPitch("D", 0, 5),
    )
    part = ScorePart(
        "flute",
        "Flute",
        "flute",
        ("flute:staff",),
        (note1, rest, note2),
    )
    score = assemble_score(score_id="beam:rest", title="Rest Break", parts=(part,))

    root = ET.fromstring(
        score_to_musicxml(score, build_default_engraving_plan(score))
    )
    rest_note = next(
        note
        for note in root.findall(".//part[@id='flute']/measure/note")
        if note.find("rest") is not None
    )

    assert rest_note.find("beam") is None



def test_musicxml_polyphonic_voices_keep_ties_and_beams_independent():
    voice1 = (
        ScoreEvent(
            event_id="v1:a",
            part_id="p",
            staff_id="s",
            voice_id="voice1",
            kind=NotatedAtomKind.NOTE,
            span=ScoreSpan(Fraction(0), Fraction(1, 2)),
            source_event_ids=("src:v1:a",),
            written_pitch=WrittenPitch("C", 0, 5),
        ),
        ScoreEvent(
            event_id="v1:b",
            part_id="p",
            staff_id="s",
            voice_id="voice1",
            kind=NotatedAtomKind.NOTE,
            span=ScoreSpan(Fraction(1, 2), Fraction(1, 2)),
            source_event_ids=("src:v1:b",),
            written_pitch=WrittenPitch("D", 0, 5),
        ),
    )
    voice2 = (
        ScoreEvent(
            event_id="v2:a",
            part_id="p",
            staff_id="s",
            voice_id="voice2",
            kind=NotatedAtomKind.NOTE,
            span=ScoreSpan(Fraction(0), Fraction(1)),
            source_event_ids=("src:v2",),
            written_pitch=WrittenPitch("G", 0, 4),
            tie_to_next=True,
        ),
        ScoreEvent(
            event_id="v2:b",
            part_id="p",
            staff_id="s",
            voice_id="voice2",
            kind=NotatedAtomKind.NOTE,
            span=ScoreSpan(Fraction(1), Fraction(1)),
            source_event_ids=("src:v2",),
            written_pitch=WrittenPitch("G", 0, 4),
            tie_from_previous=True,
        ),
    )
    part = ScorePart(
        "p",
        "Piano Upper",
        "future_instrument",
        ("s",),
        voice1 + voice2,
    )
    score = assemble_score(score_id="poly:voice-safe", title="Voice Safe", parts=(part,))
    plan = build_default_engraving_plan(score)

    root = ET.fromstring(score_to_musicxml(score, plan))
    measure = root.find(".//part[@id='p']/measure")
    assert measure is not None
    assert measure.find("backup") is not None

    notes = measure.findall("note")
    voice1_notes = [n for n in notes if n.findtext("voice") == "voice1"]
    voice2_notes = [n for n in notes if n.findtext("voice") == "voice2"]

    assert [n.findtext("beam[@number='1']") for n in voice1_notes] == [
        "begin",
        "end",
    ]
    assert all(n.find("tie") is None for n in voice1_notes)
    assert voice2_notes[0].find("tie[@type='start']") is not None
    assert voice2_notes[1].find("tie[@type='stop']") is not None
    assert all(n.find("beam") is None for n in voice2_notes)
