import json
from pathlib import Path
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


EXPECTED = json.loads(
    Path("tests/golden/transcription_8bar_expected.json").read_text(encoding="utf-8")
)


def _event(event_id, beat, midi, dynamic, phrase, duration=.9):
    return CommittedPerformanceEvent(
        event_id=event_id,
        player_id="flute",
        instrument="flute",
        commitment=CommitmentState.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=beat * .5,
            offset_seconds=beat * .5 + .46,
            transport_beat=beat,
            transport_offset_beat=beat + duration,
        ),
        pitch=PerformedPitch(nominal_midi=float(midi)),
        dynamic=dynamic,
        phrase_context_id=phrase,
        provenance=("golden:performance-evidence",),
    )


def test_golden_8bar_phrase_has_stable_readable_structure():
    engine = NotationEngine()
    request = PartTranscriptionRequest(
        part_id="fl",
        name="Flute",
        instrument="flute",
        events=(
            _event("a1", 0, 72, .30, "A"),
            _event("a2", 1, 74, .36, "A"),
            _event("a3", 2, 76, .43, "A"),
            _event("a4", 3, 77, .52, "A"),
            _event("a5", 4, 79, .54, "A"),
            _event("a6", 6.5, 81, .56, "A", duration=1.5),
            _event("b1", 16, 81, .72, "B"),
            _event("b2", 17, 79, .66, "B"),
            _event("b3", 18, 77, .59, "B"),
            _event("b4", 19, 76, .51, "B"),
            _event("b5", 20, 74, .46, "B"),
            _event("b6", 22, 72, .40, "B"),
        ),
        staffs=(StaffProfile("fl:staff", "fl"),),
        end_beat=float(EXPECTED["score_end_beat"]),
    )

    result, xml = engine.transcribe_take_musicxml(
        (request,),
        score_id="golden:8bar",
        title=EXPECTED["title"],
        key_signature=ScoreKeySignature(EXPECTED["key_fifths"], "major"),
    )
    root = ET.fromstring(xml)
    part_xml = root.find(".//part[@id='fl']")
    assert part_xml is not None

    assert len(part_xml.findall("./measure")) == EXPECTED["measures"]
    notes = part_xml.findall("./measure/note")
    pitched = [note for note in notes if note.find("pitch") is not None]
    rests = [note for note in notes if note.find("rest") is not None]
    assert len(pitched) == EXPECTED["note_count"]
    assert len(rests) >= EXPECTED["rest_count_min"]
    assert len(part_xml.findall(".//tie[@type='start']")) == EXPECTED["tie_start_count"]
    assert len(part_xml.findall(".//tie[@type='stop']")) == EXPECTED["tie_stop_count"]

    wedges = part_xml.findall("./measure/direction/direction-type/wedge")
    assert [w.get("type") for w in wedges] == EXPECTED["wedge_types"]

    assert (
        part_xml.findtext("./measure/attributes/key/fifths")
        == str(EXPECTED["key_fifths"])
    )

    for event in result.score.parts[0].events:
        measure_index = int(event.span.onset // 4)
        assert event.span.offset <= (measure_index + 1) * 4
