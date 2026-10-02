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
from music_intelligence.transcribe.score import ScorePart, assemble_score


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
