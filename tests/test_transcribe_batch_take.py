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



def test_batch_take_materializes_readable_rests_in_voice_gaps():
    engine = NotationEngine()
    request = PartTranscriptionRequest(
        part_id="fl",
        name="Flute",
        instrument="flute",
        events=(
            _event("fl:late1", "flute", 72, 1),
            _event("fl:late2", "flute", 74, 3),
        ),
        staffs=(StaffProfile("fl:staff", "fl"),),
    )

    result, xml = engine.transcribe_take_musicxml(
        (request,),
        score_id="take:rests",
        title="Readable Rests",
    )

    rests = [
        event
        for event in result.score.parts[0].events
        if event.kind.value == "rest"
    ]
    assert len(rests) >= 2

    root = ET.fromstring(xml)
    assert root.findall(".//part[@id='fl']/measure/note/rest")


def test_batch_piano_gesture_becomes_true_musicxml_chord():
    engine = NotationEngine()

    def piano_event(event_id, midi, seconds):
        return CommittedPerformanceEvent(
            event_id=event_id,
            player_id="piano",
            instrument="piano",
            commitment=CommitmentState.PLAYED,
            time=PerformanceTimeSpan(
                onset_seconds=seconds,
                offset_seconds=seconds + .45,
                transport_beat=0.0,
                transport_offset_beat=1.0,
            ),
            pitch=PerformedPitch(nominal_midi=float(midi)),
            dynamic=.5,
            gesture_id="gesture:triad",
            provenance=("test:performance-evidence",),
        )

    request = PartTranscriptionRequest(
        part_id="pn",
        name="Piano",
        instrument="piano",
        events=(
            piano_event("pn:c", 60, 0.000),
            piano_event("pn:e", 64, 0.014),
            piano_event("pn:g", 67, 0.026),
        ),
        staffs=(
            StaffProfile("pn:upper", "upper"),
            StaffProfile("pn:lower", "lower"),
        ),
    )

    result, xml = engine.transcribe_take_musicxml(
        (request,),
        score_id="take:piano-chord",
        title="Piano Chord",
    )

    assert result.parts[0].piano_gestures
    assert result.parts[0].piano_gestures[0].kind == "simultaneous_chord"
    root = ET.fromstring(xml)
    assert len(root.findall(".//part[@id='pn']/measure/note/chord")) == 2


def test_batch_take_infers_dynamic_hairpin_and_exports_wedge():
    engine = NotationEngine()

    def dyn_event(event_id, beat, dynamic):
        event = _event(event_id, "flute", 72 + int(beat), beat)
        return CommittedPerformanceEvent(
            event_id=event.event_id,
            player_id=event.player_id,
            instrument=event.instrument,
            commitment=event.commitment,
            time=event.time,
            pitch=event.pitch,
            dynamic=dynamic,
            provenance=event.provenance,
        )

    request = PartTranscriptionRequest(
        part_id="fl",
        name="Flute",
        instrument="flute",
        events=(
            dyn_event("fl:d1", 0, .30),
            dyn_event("fl:d2", 1, .37),
            dyn_event("fl:d3", 2, .45),
            dyn_event("fl:d4", 3, .54),
        ),
        staffs=(StaffProfile("fl:staff", "fl"),),
    )

    result, xml = engine.transcribe_take_musicxml(
        (request,),
        score_id="take:hairpin",
        title="Hairpin Take",
    )

    assert len(result.score.spanners) == 1
    root = ET.fromstring(xml)
    wedges = root.findall(".//part[@id='fl']/measure/direction/direction-type/wedge")
    assert [w.get("type") for w in wedges] == ["crescendo", "stop"]



def test_dynamic_hairpins_are_segmented_across_large_gaps():
    engine = NotationEngine()

    def dyn(event_id, beat, dynamic):
        event = _event(event_id, "flute", 72, beat)
        return CommittedPerformanceEvent(
            event_id=event.event_id,
            player_id=event.player_id,
            instrument=event.instrument,
            commitment=event.commitment,
            time=event.time,
            pitch=event.pitch,
            dynamic=dynamic,
            provenance=event.provenance,
        )

    request = PartTranscriptionRequest(
        part_id="fl",
        name="Flute",
        instrument="flute",
        events=(
            dyn("a1", 0, .30),
            dyn("a2", 1, .38),
            dyn("a3", 2, .50),
            dyn("b1", 10, .70),
            dyn("b2", 11, .60),
            dyn("b3", 12, .48),
        ),
        staffs=(StaffProfile("fl:staff", "fl"),),
    )

    result = engine.transcribe_take(
        (request,),
        score_id="take:segmented-dynamics",
        title="Segmented Dynamics",
    )

    assert len(result.parts[0].dynamic_trajectories) == 2
    assert len(result.score.spanners) == 2



def _polyphonic_piano_event(event_id, beat, duration, midi, voice_role):
    return CommittedPerformanceEvent(
        event_id=event_id,
        player_id="piano",
        instrument="piano",
        commitment=CommitmentState.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=float(beat) * .5,
            offset_seconds=float(beat + duration) * .5,
            transport_beat=float(beat),
            transport_offset_beat=float(beat + duration),
        ),
        pitch=PerformedPitch(nominal_midi=float(midi)),
        voice_role=voice_role,
        dynamic=.5,
        provenance=("test:polyphonic-piano",),
    )


def test_polyphonic_piano_secondary_voice_rests_stay_within_active_bar():
    engine = NotationEngine()
    upper = StaffProfile(
        "pn:upper",
        "upper",
        role_tags=frozenset({"voice1", "voice2"}),
        nominal_low_midi=60,
        nominal_high_midi=108,
    )
    lower = StaffProfile(
        "pn:lower",
        "lower",
        role_tags=frozenset({"bass"}),
        nominal_low_midi=21,
        nominal_high_midi=59,
    )
    request = PartTranscriptionRequest(
        part_id="pn",
        name="Piano",
        instrument="piano",
        events=(
            _polyphonic_piano_event("v1:a", 0, 2, 76, "voice1"),
            _polyphonic_piano_event("v1:b", 2, 2, 79, "voice1"),
            _polyphonic_piano_event("v2:a", 1, 1, 67, "voice2"),
        ),
        staffs=(upper, lower),
        end_beat=8.0,
        infer_piano_gestures=False,
        infer_dynamic_hairpins=False,
    )

    result = engine.transcribe_part(request)
    upper_events = [
        event
        for event in result.part.events
        if event.staff_id == "pn:upper"
    ]
    voice_ids = sorted({event.voice_id for event in upper_events})
    assert len(voice_ids) == 2
    primary_voice = next(
        event.voice_id
        for event in upper_events
        if "v1:a" in event.source_event_ids
    )
    secondary_voice = next(
        event.voice_id
        for event in upper_events
        if "v2:a" in event.source_event_ids
    )

    secondary_rests = [
        event
        for event in upper_events
        if event.voice_id == secondary_voice and event.kind.value == "rest"
    ]
    assert secondary_rests
    assert all(event.span.offset <= 4 for event in secondary_rests)

    primary_rests = [
        event
        for event in upper_events
        if event.voice_id == primary_voice and event.kind.value == "rest"
    ]
    assert any(event.span.onset >= 4 for event in primary_rests)


def test_polyphonic_piano_overlapping_voices_get_opposing_stems_and_musicxml_backup():
    engine = NotationEngine()
    upper = StaffProfile(
        "pn:upper",
        "upper",
        role_tags=frozenset({"voice1", "voice2"}),
        nominal_low_midi=60,
        nominal_high_midi=108,
    )
    lower = StaffProfile(
        "pn:lower",
        "lower",
        role_tags=frozenset({"bass"}),
        nominal_low_midi=21,
        nominal_high_midi=59,
    )
    request = PartTranscriptionRequest(
        part_id="pn",
        name="Piano",
        instrument="piano",
        events=(
            _polyphonic_piano_event("upper:sustain", 0, 2, 76, "voice1"),
            _polyphonic_piano_event("lower:entry", 1, 1, 67, "voice2"),
        ),
        staffs=(upper, lower),
        end_beat=4.0,
        infer_piano_gestures=False,
        infer_dynamic_hairpins=False,
    )

    result, xml = engine.transcribe_take_musicxml(
        (request,),
        score_id="take:polyphonic-piano",
        title="Polyphonic Piano",
    )
    plan = engine.engraving_plan(result.score)

    source_to_stem = {}
    by_event = {intent.event_id: intent for intent in plan.intents}
    for event in result.score.parts[0].events:
        if event.source_event_ids:
            source_to_stem[event.source_event_ids[0]] = by_event[event.event_id].stem_direction.value

    assert source_to_stem["upper:sustain"] == "up"
    assert source_to_stem["lower:entry"] == "down"

    root = ET.fromstring(xml)
    piano_measure = root.find(".//part[@id='pn']/measure")
    assert piano_measure is not None
    assert piano_measure.find("backup") is not None
    stems = [
        note.findtext("stem")
        for note in piano_measure.findall("note")
        if note.find("pitch") is not None
    ]
    assert "up" in stems
    assert "down" in stems
