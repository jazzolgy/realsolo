from fractions import Fraction
from xml.etree import ElementTree as ET

from music_intelligence.transcribe.musicxml import score_to_musicxml
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import (
    ScoreEvent,
    ScorePart,
    ScoreSpanner,
    ScoreSpannerKind,
    assemble_score,
)
from music_intelligence.transcribe.spelling import WrittenPitch


def _note(event_id, onset):
    return ScoreEvent(
        event_id=event_id,
        part_id="vln",
        staff_id="staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(onset), Fraction(1)),
        source_event_ids=(f"src:{event_id}",),
        written_pitch=WrittenPitch("A", 0, 4),
    )


def test_musicxml_exports_crescendo_wedge_start_and_stop():
    part = ScorePart(
        "vln",
        "Violin",
        "violin",
        ("staff",),
        (_note("a", 0), _note("b", 2)),
        profile_id="violin",
    )
    score = assemble_score(
        score_id="hairpin",
        title="Hairpin",
        parts=(part,),
        spanners=(
            ScoreSpanner(
                "hp:1",
                ScoreSpannerKind.CRESCENDO,
                "vln",
                "a",
                "b",
            ),
        ),
    )

    root = ET.fromstring(score_to_musicxml(score))
    wedges = root.findall(".//direction/direction-type/wedge")

    assert [(w.get("type"), w.get("number")) for w in wedges] == [
        ("crescendo", "1"),
        ("stop", "1"),
    ]


def test_musicxml_exports_diminuendo_wedge():
    part = ScorePart(
        "vln",
        "Violin",
        "violin",
        ("staff",),
        (_note("a", 0), _note("b", 2)),
        profile_id="violin",
    )
    score = assemble_score(
        score_id="hairpin:dim",
        title="Dim",
        parts=(part,),
        spanners=(
            ScoreSpanner(
                "hp:dim",
                ScoreSpannerKind.DIMINUENDO,
                "vln",
                "a",
                "b",
                placement="above",
            ),
        ),
    )

    root = ET.fromstring(score_to_musicxml(score))
    direction = root.find(".//direction")
    wedge = direction.find("./direction-type/wedge")

    assert direction.get("placement") == "above"
    assert wedge.get("type") == "diminuendo"
