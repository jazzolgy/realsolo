import json
import pytest

from music_intelligence.reasoning.legend_style_core import CandidateEvent, MusicalContextVector
from music_intelligence.reasoning.online_improviser import SoftPlan
from music_intelligence.reasoning.polyphonic_event import (
    BassRelation,
    DoublingRelation,
    InstrumentAssignment,
    PolyphonicEventCandidate,
    TopNoteConstraint,
    VoiceEvent,
    VoiceLeadingRelation,
)
from music_intelligence.reasoning.polyphonic_online import (
    PolyphonicOnlineEvaluator,
    PolyphonicPerformanceMemory,
    perform_one_polyphonic_event,
)


def make_voicing() -> PolyphonicEventCandidate:
    return PolyphonicEventCandidate(
        voices=(
            VoiceEvent("bass", 48, harmonic_role="root", assignment=InstrumentAssignment(instrument_family="piano")),
            VoiceEvent("tenor", 55, harmonic_role="5"),
            VoiceEvent("alto", 59, harmonic_role="7"),
            VoiceEvent("soprano", 64, harmonic_role="3", onset_offset_beats=.02),
        ),
        duration_beats=1.0,
        tags=frozenset({"guide_tones"}),
        role="comping",
        top_note_constraint=TopNoteConstraint(target_pitch_midi=64, voice_id="soprano"),
        bass_relation=BassRelation("bass", harmonic_role="root", interval_from_root=0),
        doublings=(DoublingRelation(("bass", "soprano"), relation="semantic_example"),),
        voice_leading=(VoiceLeadingRelation("soprano", "soprano", semitone_motion=1),),
        provenance=("unit_test",),
    )


def test_existing_monophonic_candidate_event_is_unchanged():
    event = CandidateEvent(60, .5)
    assert event.pitch_midi == 60
    assert not hasattr(event, "voices")


def test_polyphonic_candidate_represents_order_register_spacing_and_assignments():
    v = make_voicing()
    v.validate()
    assert [x.voice_id for x in v.ordered_voices] == ["bass", "tenor", "alto", "soprano"]
    assert v.pitches_midi == (48, 55, 59, 64)
    assert v.register_span_semitones == 16
    assert v.spacing_semitones == (7, 4, 5)
    assert v.voices[0].assignment.instrument_family == "piano"


def test_voice_identity_and_order_survive_json_serialization():
    original = make_voicing()
    payload = json.loads(json.dumps(original.to_dict()))
    restored = PolyphonicEventCandidate.from_dict(payload)
    assert [v.voice_id for v in restored.voices] == [v.voice_id for v in original.voices]
    assert restored.pitches_midi == original.pitches_midi
    assert restored.doublings[0].voice_ids == ("bass", "soprano")
    assert restored.voice_leading[0].from_voice_id == "soprano"


def test_core_has_no_piano_range_or_hand_semantics():
    v = PolyphonicEventCandidate(
        voices=(VoiceEvent("v1", 10, assignment=InstrumentAssignment(instrument_family="contrabass")),),
        duration_beats=.5,
    )
    v.validate()
    assert not hasattr(v, "left_hand")
    assert not hasattr(v, "right_hand")


def test_polyphonic_commit_is_one_atomic_immediate_action():
    plan = SoftPlan(4, "support soloist", candidate_families=("sparse_shell",))
    memory = PolyphonicPerformanceMemory()
    result = perform_one_polyphonic_event(
        plan,
        PolyphonicOnlineEvaluator(),
        [make_voicing()],
        MusicalContextVector(),
        memory,
    )
    assert result.candidate is memory.committed[0]
    assert len(memory.committed) == 1


def test_soft_plan_still_cannot_freeze_future_notes_for_polyphony():
    plan = SoftPlan(8, "build", exact_future_notes=(60, 64, 67))
    with pytest.raises(ValueError):
        perform_one_polyphonic_event(
            plan,
            PolyphonicOnlineEvaluator(),
            [make_voicing()],
            MusicalContextVector(),
            PolyphonicPerformanceMemory(),
        )


def test_voice_leading_uses_identity_not_piano_specific_nearest_note_matching():
    memory = PolyphonicPerformanceMemory()
    previous = PolyphonicEventCandidate(
        voices=(VoiceEvent("low", 48), VoiceEvent("top", 64)),
        duration_beats=1,
    )
    memory.commit(previous)
    compact = PolyphonicEventCandidate(
        voices=(VoiceEvent("low", 50), VoiceEvent("top", 65)),
        duration_beats=1,
    )
    displaced = PolyphonicEventCandidate(
        voices=(VoiceEvent("low", 60), VoiceEvent("top", 76)),
        duration_beats=1,
    )
    ev = PolyphonicOnlineEvaluator()
    ctx = MusicalContextVector()
    assert ev.evaluate(compact, ctx, memory).total > ev.evaluate(displaced, ctx, memory).total
