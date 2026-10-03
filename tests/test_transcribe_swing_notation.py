from xml.etree import ElementTree as ET
from fractions import Fraction

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
from music_intelligence.transcribe.pipeline import (
    basic_rhythm_candidates,
    notation_intent_from_event,
)


def _event(event_id, *, metadata=None):
    return CommittedPerformanceEvent(
        event_id=event_id,
        player_id="sax",
        instrument="alto_sax",
        commitment=PerformanceCommitment.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=.33,
            offset_seconds=.50,
            transport_beat=2 / 3,
            transport_offset_beat=1.0,
        ),
        pitch=PerformedPitch(nominal_midi=69),
        metadata=metadata or {},
        provenance=("test:swing-notation",),
    )


def test_swing_context_suppresses_literal_triplet_candidate():
    event = _event("swing:offbeat")
    intent = notation_intent_from_event(event)

    candidates = basic_rhythm_candidates(
        event,
        intent,
        rhythm_context=RhythmNotationContext(RhythmicFeel.SWING),
    )

    assert all(candidate.atoms[0].tuplet is None for candidate in candidates)
    preferred = min(candidates, key=lambda candidate: candidate.total_cost)
    assert preferred.candidate_id.endswith(":eighth")
    assert preferred.atoms[0].span.onset == Fraction(1, 2)


def test_auto_context_keeps_triplet_as_an_alternative():
    event = _event("auto:offbeat")
    intent = notation_intent_from_event(event)

    candidates = basic_rhythm_candidates(
        event,
        intent,
        rhythm_context=RhythmNotationContext(RhythmicFeel.AUTO),
    )

    assert any(candidate.atoms[0].tuplet is not None for candidate in candidates)


def test_explicit_triplet_overrides_swing_written_eighth_policy():
    event = _event(
        "swing:explicit-triplet",
        metadata={"notation_tuplet": "3:2"},
    )
    engine = NotationEngine()

    result = engine.project_pitched_event(
        event,
        part_id="sax",
        staffs=(StaffProfile("sax:staff", "sax"),),
        rhythm_context=RhythmNotationContext(RhythmicFeel.SWING),
    )

    assert result.preferred_rhythm.atoms[0].tuplet is not None
    assert result.preferred_rhythm.atoms[0].tuplet.actual == 3
    assert result.preferred_rhythm.atoms[0].tuplet.normal == 2
    assert result.score_events[0].tuplet is not None


def test_batch_part_applies_shared_swing_notation_context():
    event = _event("batch:swing")
    engine = NotationEngine()
    request = PartTranscriptionRequest(
        part_id="sax",
        name="Alto Sax",
        instrument="alto_sax",
        events=(event,),
        staffs=(StaffProfile("sax:staff", "sax"),),
        rhythm_context=RhythmNotationContext(RhythmicFeel.SWING),
        materialize_rests=False,
        infer_dynamic_hairpins=False,
    )

    result = engine.transcribe_part(request)

    assert result.projections[0].preferred_rhythm.candidate_id.endswith(":eighth")
    assert result.part.events[0].tuplet is None



def test_swing_take_emits_one_global_swing_direction():
    engine = NotationEngine()
    request = PartTranscriptionRequest(
        part_id="sax",
        name="Alto Sax",
        instrument="alto_sax",
        events=(_event("take:swing"),),
        staffs=(StaffProfile("sax:staff", "sax"),),
        rhythm_context=RhythmNotationContext(RhythmicFeel.SWING),
        materialize_rests=False,
        infer_dynamic_hairpins=False,
    )

    result, xml = engine.transcribe_take_musicxml(
        (request,),
        score_id="swing:take",
        title="Swing Take",
    )

    assert [direction.text for direction in result.score.directions] == ["Swing"]
    root = ET.fromstring(xml)
    assert root.findall(".//direction/direction-type/words")[0].text == "Swing"
    assert len(root.findall(".//direction/direction-type/words")) == 1


def test_mixed_feel_take_does_not_invent_global_swing_direction():
    engine = NotationEngine()
    swing = PartTranscriptionRequest(
        part_id="sax1",
        name="Alto Sax 1",
        instrument="alto_sax",
        events=(_event("mixed:swing"),),
        staffs=(StaffProfile("sax1:staff", "sax"),),
        rhythm_context=RhythmNotationContext(RhythmicFeel.SWING),
        materialize_rests=False,
        infer_dynamic_hairpins=False,
    )
    straight = PartTranscriptionRequest(
        part_id="sax2",
        name="Alto Sax 2",
        instrument="alto_sax",
        events=(_event("mixed:straight"),),
        staffs=(StaffProfile("sax2:staff", "sax"),),
        rhythm_context=RhythmNotationContext(RhythmicFeel.STRAIGHT),
        materialize_rests=False,
        infer_dynamic_hairpins=False,
    )

    result = engine.transcribe_take(
        (swing, straight),
        score_id="mixed:take",
        title="Mixed Feel",
    )

    assert result.score.directions == ()


def test_explicit_triplet_reaches_musicxml_as_time_modification():
    event = _event(
        "xml:explicit-triplet",
        metadata={"notation_tuplet": "3:2"},
    )
    engine = NotationEngine()
    request = PartTranscriptionRequest(
        part_id="sax",
        name="Alto Sax",
        instrument="alto_sax",
        events=(event,),
        staffs=(StaffProfile("sax:staff", "sax"),),
        rhythm_context=RhythmNotationContext(RhythmicFeel.SWING),
        materialize_rests=False,
        infer_dynamic_hairpins=False,
    )

    _, xml = engine.transcribe_take_musicxml(
        (request,),
        score_id="triplet:take",
        title="Explicit Triplet",
    )

    root = ET.fromstring(xml)
    note = root.find(".//part[@id='sax']/measure/note")
    assert note.findtext("type") == "eighth"
    assert note.findtext("time-modification/actual-notes") == "3"
    assert note.findtext("time-modification/normal-notes") == "2"
