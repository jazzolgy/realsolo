from fractions import Fraction
from xml.etree import ElementTree as ET

from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    NotationEngine,
    PartTranscriptionRequest,
    PerformanceTimeSpan,
    PerformedPitch,
    RhythmNotationContext,
    RhythmicFeel,
)
from music_intelligence.transcribe.allocation import StaffProfile
from music_intelligence.transcribe.events import PerformanceCommitment


def _swing_note(event_id, onset, offset, midi):
    return CommittedPerformanceEvent(
        event_id=event_id,
        player_id="alto",
        instrument="alto_sax",
        commitment=PerformanceCommitment.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=float(onset) * .5,
            offset_seconds=float(offset) * .5,
            transport_beat=float(onset),
            transport_offset_beat=float(offset),
        ),
        pitch=PerformedPitch(nominal_midi=float(midi)),
        provenance=("golden:swing-performance",),
    )


def test_golden_four_bar_swing_is_written_as_straight_eighths_with_swing_mark():
    events = []
    midi = 67
    event_index = 0
    for bar in range(4):
        bar_start = Fraction(bar * 4)
        for beat in range(4):
            beat_start = bar_start + beat
            events.append(
                _swing_note(
                    f"s{event_index}",
                    beat_start,
                    beat_start + Fraction(2, 3),
                    midi,
                )
            )
            event_index += 1
            events.append(
                _swing_note(
                    f"s{event_index}",
                    beat_start + Fraction(2, 3),
                    beat_start + 1,
                    midi + 2,
                )
            )
            event_index += 1
            midi = 67 + ((midi - 65) % 7)

    engine = NotationEngine()
    request = PartTranscriptionRequest(
        part_id="alto",
        name="Alto Sax",
        instrument="alto_sax",
        events=tuple(events),
        staffs=(StaffProfile("alto:staff", "alto"),),
        rhythm_context=RhythmNotationContext(RhythmicFeel.SWING),
        materialize_rests=False,
        infer_dynamic_hairpins=False,
        end_beat=16.0,
    )

    result, xml = engine.transcribe_take_musicxml(
        (request,),
        score_id="golden:swing:4bar",
        title="Golden 4-Bar Swing",
    )
    root = ET.fromstring(xml)
    part = root.find(".//part[@id='alto']")
    assert part is not None

    assert [direction.text for direction in result.score.directions] == ["Swing"]
    assert part.findtext("./measure/direction/direction-type/words") == "Swing"
    assert len(part.findall("./measure")) == 4

    notes = part.findall("./measure/note")
    assert len(notes) == 32
    assert all(note.findtext("type") == "eighth" for note in notes)
    assert all(note.find("time-modification") is None for note in notes)

    for measure in part.findall("./measure"):
        beam_values = [
            note.findtext("beam[@number='1']")
            for note in measure.findall("note")
        ]
        assert beam_values == [
            "begin",
            "continue",
            "continue",
            "end",
            "begin",
            "continue",
            "continue",
            "end",
        ]
