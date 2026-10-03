from xml.etree import ElementTree as ET

from music_intelligence.transcribe.allocation import StaffProfile
from music_intelligence.transcribe.events import (
    CommittedPerformanceEvent,
    PerformedPitch,
    PerformanceCommitment,
    PerformanceTimeSpan,
)
from music_intelligence.transcribe.product import TranscriptionNotationEngine


def test_product_pipeline_reaches_logical_score_engraving_and_musicxml():
    engine = TranscriptionNotationEngine()
    event = CommittedPerformanceEvent(
        event_id="take:1:piano:1",
        player_id="source",
        instrument="piano",
        commitment=PerformanceCommitment.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=0.0,
            offset_seconds=0.48,
            transport_beat=0.02,
            transport_offset_beat=0.98,
        ),
        pitch=PerformedPitch(nominal_midi=60),
        voice_role="melody",
        articulation=("accent",),
        provenance=("test-source",),
    )

    result = engine.transcribe_event(
        event,
        staffs=(
            StaffProfile("piano:upper", "piano", frozenset({"melody"}), 55, 108),
            StaffProfile("piano:lower", "piano", frozenset({"bass"}), 21, 67),
        ),
    )
    score = engine.logical_score_for_part(
        (result,),
        score_id="score:take:1",
        title="Take 1",
        part_id="piano",
        part_name="Piano",
        instrument="piano",
        staff_ids=("piano:upper", "piano:lower"),
        profile_id="piano",
    )
    plan = engine.engraving_plan(score)
    xml = engine.musicxml(score, engraving_plan=plan)
    root = ET.fromstring(xml)

    assert score.parts[0].events[0].written_pitch.name == "C4"
    assert plan.score_id == score.score_id
    assert root.tag == "score-partwise"
    assert root.findtext("./work/work-title") == "Take 1"
    assert root.find(".//pitch/step").text == "C"


def test_product_pipeline_supports_unpitched_performance_evidence():
    from music_intelligence.transcribe.events import UnpitchedToken

    engine = TranscriptionNotationEngine()
    event = CommittedPerformanceEvent(
        event_id="take:1:drums:1",
        player_id="source",
        instrument="drum_set",
        commitment=PerformanceCommitment.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=0.0,
            offset_seconds=0.1,
            transport_beat=0.0,
            transport_offset_beat=0.5,
        ),
        unpitched=UnpitchedToken("snare", instrument_family="drums", technique="ghost"),
        technique=("ghost_note",),
    )

    result = engine.transcribe_event(event)
    score = engine.logical_score_for_part(
        (result,),
        score_id="score:drums",
        title="Drum Take",
        part_id="drums",
        part_name="Drums",
        instrument="drum_set",
        staff_ids=("drums:staff",),
    )

    score_event = score.parts[0].events[0]
    assert score_event.unpitched.token == "snare"
    assert score_event.written_pitch is None
