from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    PerformedPitch,
    PerformanceTimeSpan,
)
from music_intelligence.transcribe.piano import piano_gesture_candidates


def event(event_id, onset, midi, technique=()):
    return CommittedPerformanceEvent(
        event_id=event_id,
        player_id="piano",
        instrument="piano",
        commitment=CommitmentState.COMMITTED,
        time=PerformanceTimeSpan(onset, onset + .5),
        pitch=PerformedPitch(nominal_midi=midi),
        gesture_id="piano:g1",
        technique=technique,
    )


def test_small_stagger_can_be_notated_as_one_chord_not_literal_offsets():
    events = (
        event("n1", 1.000, 60),
        event("n2", 1.018, 64),
        event("n3", 1.029, 67),
    )
    best = piano_gesture_candidates(events)[0]
    assert best.kind == "simultaneous_chord"


def test_explicit_roll_evidence_prefers_arpeggiated_chord():
    events = (
        event("n1", 1.000, 48, ("rolled",)),
        event("n2", 1.045, 55, ("rolled",)),
        event("n3", 1.082, 64, ("rolled",)),
    )
    best = piano_gesture_candidates(events)[0]
    assert best.kind == "arpeggiated_chord"
    assert "arpeggiate" in best.markings


def test_large_structural_stagger_retains_separate_onset_candidate():
    events = (
        event("n1", 1.000, 60),
        event("n2", 1.180, 67),
    )
    candidates = piano_gesture_candidates(events)
    assert any(c.kind == "separate_onsets" for c in candidates)
