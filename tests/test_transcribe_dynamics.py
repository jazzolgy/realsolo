from fractions import Fraction
from xml.etree import ElementTree as ET

from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe.allocation import StaffProfile
from music_intelligence.transcribe.events import (
    CommittedPerformanceEvent,
    PerformedPitch,
    PerformanceTimeSpan,
)
from music_intelligence.transcribe.musicxml import score_to_musicxml
from music_intelligence.transcribe.projection import (
    dynamic_marking_from_level,
    project_pitched_event,
)
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import ScoreEvent, ScorePart, assemble_score
from music_intelligence.transcribe.spelling import WrittenPitch


def test_dynamic_level_is_coarsened_to_readable_marking():
    assert dynamic_marking_from_level(.05) == "pp"
    assert dynamic_marking_from_level(.35) == "mp"
    assert dynamic_marking_from_level(.55) == "mf"
    assert dynamic_marking_from_level(.90) == "ff"


def test_projected_dynamic_reaches_musicxml_direction():
    event = CommittedPerformanceEvent(
        event_id="cl:1",
        player_id="cl",
        instrument="clarinet_bb",
        commitment=CommitmentState.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=0.0,
            offset_seconds=.5,
            transport_beat=0.0,
            transport_offset_beat=1.0,
        ),
        pitch=PerformedPitch(nominal_midi=72),
        dynamic=.55,
    )
    projection = project_pitched_event(
        event,
        part_id="cl",
        staffs=(StaffProfile("staff", "cl"),),
    )
    part = ScorePart(
        "cl",
        "Clarinet in Bb",
        "clarinet_bb",
        ("staff",),
        projection.score_events,
        profile_id="clarinet_bb",
    )
    score = assemble_score(score_id="dyn:1", title="Dynamics", parts=(part,))
    root = ET.fromstring(score_to_musicxml(score))

    assert projection.score_events[0].dynamic_marking == "mf"
    assert root.find(".//direction/direction-type/dynamics/mf") is not None



def _score_note(event_id, onset, dynamic, *, group=None):
    return ScoreEvent(
        event_id=event_id,
        part_id="vln",
        staff_id="staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(onset), Fraction(1)),
        source_event_ids=(f"src:{event_id}",),
        written_pitch=WrittenPitch("A", 0, 4),
        simultaneity_group_id=group,
        dynamic_marking=dynamic,
    )


def _dynamic_names(xml):
    root = ET.fromstring(xml)
    result = []
    for dynamics in root.findall(".//direction/direction-type/dynamics"):
        if list(dynamics):
            result.append(list(dynamics)[0].tag)
    return result


def test_repeated_same_dynamic_is_emitted_once():
    part = ScorePart(
        "vln",
        "Violin",
        "violin",
        ("staff",),
        (
            _score_note("n1", 0, "mf"),
            _score_note("n2", 1, "mf"),
            _score_note("n3", 2, "mf"),
        ),
        profile_id="violin",
    )
    score = assemble_score(score_id="dyn:repeat", title="Repeat", parts=(part,))

    assert _dynamic_names(score_to_musicxml(score)) == ["mf"]


def test_meaningful_dynamic_change_is_preserved():
    part = ScorePart(
        "vln",
        "Violin",
        "violin",
        ("staff",),
        (
            _score_note("n1", 0, "mf"),
            _score_note("n2", 1, "mf"),
            _score_note("n3", 2, "f"),
            _score_note("n4", 3, "f"),
        ),
        profile_id="violin",
    )
    score = assemble_score(score_id="dyn:change", title="Change", parts=(part,))

    assert _dynamic_names(score_to_musicxml(score)) == ["mf", "f"]


def test_same_dynamic_is_not_repeated_at_next_measure():
    part = ScorePart(
        "vln",
        "Violin",
        "violin",
        ("staff",),
        (
            _score_note("n1", 0, "p"),
            _score_note("n2", 4, "p"),
        ),
        profile_id="violin",
    )
    score = assemble_score(score_id="dyn:bars", title="Bars", parts=(part,))

    assert _dynamic_names(score_to_musicxml(score)) == ["p"]
