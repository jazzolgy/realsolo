from xml.etree import ElementTree as ET

from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    NotationEngine,
    PartTranscriptionRequest,
    PerformanceTimeSpan,
    PerformedPitch,
)
from music_intelligence.transcribe.allocation import StaffProfile
from music_intelligence.transcribe.events import PerformanceCommitment


def _event(event_id, beat, duration, midi, role):
    return CommittedPerformanceEvent(
        event_id=event_id,
        player_id="piano",
        instrument="piano",
        commitment=PerformanceCommitment.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=beat * .5,
            offset_seconds=(beat + duration) * .5,
            transport_beat=beat,
            transport_offset_beat=beat + duration,
        ),
        pitch=PerformedPitch(nominal_midi=float(midi)),
        voice_role=role,
        dynamic=.5,
        provenance=("golden:polyphonic-piano",),
    )


def test_golden_two_bar_polyphonic_piano_is_readable_and_voice_safe():
    upper = StaffProfile(
        "pn:upper",
        "upper",
        role_tags=frozenset({"melody", "inner"}),
        nominal_low_midi=60,
        nominal_high_midi=108,
    )
    lower = StaffProfile(
        "pn:lower",
        "lower",
        role_tags=frozenset({"bass"}),
        nominal_low_midi=21,
        nominal_high_midi=60,
    )
    request = PartTranscriptionRequest(
        part_id="pn",
        name="Piano",
        instrument="piano",
        events=(
            _event("mel:1", .5, 1.5, 72, "melody"),
            _event("mel:2", 2, 1, 76, "melody"),
            _event("mel:3", 4, 1, 79, "melody"),
            _event("mel:4", 5, 1, 77, "melody"),
            _event("inner:1", 1, 1, 64, "inner"),
            _event("inner:2", 2, 1, 67, "inner"),
            _event("bass:1", 0, 2, 48, "bass"),
            _event("bass:2", 2, 2, 43, "bass"),
            _event("bass:3", 4, 2, 45, "bass"),
            _event("bass:4", 6, 2, 43, "bass"),
        ),
        staffs=(upper, lower),
        end_beat=8.0,
        infer_piano_gestures=False,
        infer_dynamic_hairpins=False,
    )

    engine = NotationEngine()
    result, xml = engine.transcribe_take_musicxml(
        (request,),
        score_id="golden:piano:2bar",
        title="Golden Polyphonic Piano",
    )
    root = ET.fromstring(xml)
    part = root.find(".//part[@id='pn']")
    assert part is not None

    assert len(part.findall("./measure")) == 2
    assert part.findtext("./measure/attributes/staves") == "2"
    assert part.find("measure/backup") is not None
    assert part.find(".//tie[@type='start']") is not None
    assert part.find(".//tie[@type='stop']") is not None

    plan = engine.engraving_plan(result.score)
    by_id = {intent.event_id: intent for intent in plan.intents}
    melody_stems = set()
    inner_stems = set()
    for event in result.score.parts[0].events:
        if "mel:1" in event.source_event_ids or "mel:2" in event.source_event_ids:
            melody_stems.add(by_id[event.event_id].stem_direction.value)
        if "inner:1" in event.source_event_ids or "inner:2" in event.source_event_ids:
            inner_stems.add(by_id[event.event_id].stem_direction.value)

    assert melody_stems == {"up"}
    assert inner_stems == {"down"}

    lower_notes = [
        note
        for note in part.findall("./measure/note")
        if note.find("pitch") is not None and note.findtext("staff") == "2"
    ]
    assert len(lower_notes) == 4

    inner_voice_id = next(
        event.voice_id
        for event in result.score.parts[0].events
        if "inner:1" in event.source_event_ids
    )
    inner_rests = [
        event
        for event in result.score.parts[0].events
        if event.voice_id == inner_voice_id and event.kind.value == "rest"
    ]
    assert inner_rests
    assert all(event.span.offset <= 4 for event in inner_rests)
