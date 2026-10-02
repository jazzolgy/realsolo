from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    ConfidenceBundle,
    EventAlternative,
    EvidenceKind,
    EvidenceRef,
    PerformedPitch,
    PerformanceTimeSpan,
    UnpitchedToken,
)


def test_pitched_committed_event_preserves_performance_evidence_without_score_time():
    event = CommittedPerformanceEvent(
        event_id="piano:42",
        player_id="piano",
        instrument="piano",
        commitment=CommitmentState.COMMITTED,
        time=PerformanceTimeSpan(
            onset_seconds=12.031,
            offset_seconds=12.487,
            transport_beat=17.92,
        ),
        pitch=PerformedPitch(nominal_midi=64.0, cents_offset=-3.2),
        voice_role="melody",
        gesture_id="gesture:9",
        articulation=("legato",),
        confidence=ConfidenceBundle(pitch=.99, rhythm=.93, notation_relevance=.88),
        evidence=(
            EvidenceRef(EvidenceKind.PLAYER_EVENT, "player:piano:event:42"),
        ),
        provenance=("player/piano", "committed-event"),
    )
    event.validate()

    assert event.duration_seconds == 12.487 - 12.031
    assert not hasattr(event, "score_onset")
    assert not hasattr(event, "note_value")
    assert not hasattr(event, "staff")


def test_unpitched_drum_event_uses_token_instead_of_fake_pitch():
    event = CommittedPerformanceEvent(
        event_id="drums:snare:7",
        player_id="drums",
        instrument="drum_set",
        commitment=CommitmentState.PLAYED,
        time=PerformanceTimeSpan(onset_seconds=3.0),
        unpitched=UnpitchedToken("snare", instrument_family="drums", technique="ghost"),
        dynamic=.22,
        technique=("ghost_note",),
    )
    event.validate()
    assert event.pitch is None
    assert event.unpitched.token == "snare"


def test_polyphonic_gesture_may_preserve_staggered_onsets():
    first = CommittedPerformanceEvent(
        event_id="piano:g1:n1",
        player_id="piano",
        instrument="piano",
        commitment=CommitmentState.COMMITTED,
        time=PerformanceTimeSpan(5.000, 5.600),
        pitch=PerformedPitch(nominal_midi=60),
        gesture_id="piano:g1",
    )
    second = CommittedPerformanceEvent(
        event_id="piano:g1:n2",
        player_id="piano",
        instrument="piano",
        commitment=CommitmentState.COMMITTED,
        time=PerformanceTimeSpan(5.027, 5.610),
        pitch=PerformedPitch(nominal_midi=67),
        gesture_id="piano:g1",
    )
    first.validate()
    second.validate()

    assert first.gesture_id == second.gesture_id
    assert first.time.onset_seconds != second.time.onset_seconds


def test_alternatives_evidence_and_factorized_confidence_are_preserved():
    event = CommittedPerformanceEvent(
        event_id="sax:11",
        player_id="sax",
        instrument="tenor_sax",
        commitment=CommitmentState.PLAYED,
        time=PerformanceTimeSpan(8.1, 8.44),
        pitch=PerformedPitch(
            frequency_hz=466.0,
            continuous_pitch_ref="curve:sax:11",
        ),
        confidence=ConfidenceBundle(
            pitch=.86,
            rhythm=.94,
            articulation=.71,
            notation_relevance=.63,
        ),
        alternatives=(
            EventAlternative("ornament", "grace_note", .58, ("audio:seg:11",)),
            EventAlternative("ornament", "scoop", .42, ("audio:seg:11",)),
        ),
        evidence=(
            EvidenceRef(EvidenceKind.AUDIO_ANALYSIS, "audio:seg:11", confidence=.91),
        ),
    )
    event.validate()
    assert event.confidence.pitch != event.confidence.notation_relevance
    assert len(event.alternatives) == 2


def test_provisional_player_intent_is_not_transcription_input():
    event = CommittedPerformanceEvent(
        event_id="bass:future",
        player_id="bass",
        instrument="upright_bass",
        commitment=CommitmentState.PROVISIONAL,
        time=PerformanceTimeSpan(1.0, 1.2),
        pitch=PerformedPitch(nominal_midi=40),
    )
    try:
        event.validate()
    except ValueError as exc:
        assert "committed or played" in str(exc)
    else:
        raise AssertionError("provisional events must not enter transcription")


def test_event_rejects_ambiguous_pitched_and_unpitched_payload():
    event = CommittedPerformanceEvent(
        event_id="bad",
        player_id="drums",
        instrument="drum_set",
        commitment=CommitmentState.COMMITTED,
        time=PerformanceTimeSpan(1.0),
        pitch=PerformedPitch(nominal_midi=38),
        unpitched=UnpitchedToken("snare"),
    )
    try:
        event.validate()
    except ValueError as exc:
        assert "pitched or unpitched" in str(exc)
    else:
        raise AssertionError("event must not carry both pitch representations")
