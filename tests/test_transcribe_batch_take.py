from xml.etree import ElementTree as ET

from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    NotationEngine,
    PartTranscriptionRequest,
    PerformedPitch,
    PerformanceTimeSpan,
    ScoreKeySignature,
)
from music_intelligence.transcribe.allocation import StaffProfile
from music_intelligence.transcribe.spelling import PitchSpellingContext


def _event(event_id, instrument, midi, beat):
    return CommittedPerformanceEvent(
        event_id=event_id,
        player_id=instrument,
        instrument=instrument,
        commitment=CommitmentState.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=float(beat) * .5,
            offset_seconds=float(beat) * .5 + .45,
            transport_beat=float(beat),
            transport_offset_beat=float(beat) + .9,
        ),
        pitch=PerformedPitch(nominal_midi=float(midi)),
        dynamic=.55,
        provenance=("test:performance-evidence",),
    )


def test_batch_take_reaches_musicxml_with_written_transposition_and_key():
    engine = NotationEngine()

    clarinet = PartTranscriptionRequest(
        part_id="cl",
        name="Clarinet in Bb",
        instrument="clarinet_bb",
        events=(
            _event("cl:1", "clarinet_bb", 60, 0),
            _event("cl:2", "clarinet_bb", 62, 1),
        ),
        staffs=(StaffProfile("cl:staff", "cl"),),
        spelling_context=PitchSpellingContext(key_fifths=2),
    )
    flute = PartTranscriptionRequest(
        part_id="fl",
        name="Flute",
        instrument="flute",
        events=(
            _event("fl:1", "flute", 72, 0),
            _event("fl:2", "flute", 74, 1),
        ),
        staffs=(StaffProfile("fl:staff", "fl"),),
        spelling_context=PitchSpellingContext(key_fifths=0),
    )

    result = engine.transcribe_take(
        (clarinet, flute),
        score_id="take:batch:1",
        title="Batch Take",
        key_signature=ScoreKeySignature(0, "major"),
    )
    xml = engine.musicxml(result.score)
    root = ET.fromstring(xml)

    assert len(result.score.parts) == 2

    clarinet_part = result.score.parts[0]
    assert clarinet_part.events[0].written_pitch.step == "D"
    assert clarinet_part.events[1].written_pitch.step == "E"

    cl_xml = root.find(".//part[@id='cl']")
    assert cl_xml is not None
    assert cl_xml.findtext("./measure/attributes/key/fifths") == "2"
    assert cl_xml.findtext("./measure/attributes/transpose/chromatic") == "-2"
    assert [n.findtext("pitch/step") for n in cl_xml.findall("./measure/note")] == [
        "D",
        "E",
    ]

    fl_xml = root.find(".//part[@id='fl']")
    assert fl_xml is not None
    assert fl_xml.findtext("./measure/attributes/key/fifths") == "0"


def test_batch_take_consumes_only_performance_contract_shape():
    engine = NotationEngine()
    request = PartTranscriptionRequest(
        part_id="fl",
        name="Flute",
        instrument="flute",
        events=(_event("fl:1", "flute", 72, 0),),
        staffs=(StaffProfile("fl:staff", "fl"),),
    )

    result = engine.transcribe_part(request)

    assert result.part.events[0].source_event_ids == ("fl:1",)
    assert "transcribe:event-projection" in result.part.events[0].provenance



def test_engine_can_emit_musicxml_in_one_call_from_performance_evidence():
    engine = NotationEngine()
    request = PartTranscriptionRequest(
        part_id="fl",
        name="Flute",
        instrument="flute",
        events=(
            _event("fl:1", "flute", 72, 0),
            _event("fl:2", "flute", 74, 1),
        ),
        staffs=(StaffProfile("fl:staff", "fl"),),
    )

    result, xml = engine.transcribe_take_musicxml(
        (request,),
        score_id="take:one-call",
        title="One Call",
    )

    assert result.score.title == "One Call"
    assert "<score-partwise" in xml
    assert "<part-name>Flute</part-name>" in xml
