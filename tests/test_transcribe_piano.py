from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    PerformedPitch,
    PerformanceTimeSpan,
)
from fractions import Fraction

from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.piano import (
    apply_piano_gesture_candidate,
    piano_gesture_candidates,
)
from music_intelligence.transcribe.score import ScoreEvent
from music_intelligence.transcribe.spelling import WrittenPitch


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



def score_note(event_id, step):
    return ScoreEvent(
        event_id=f"score:{event_id}",
        part_id="piano",
        staff_id="upper",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1)),
        source_event_ids=(event_id,),
        written_pitch=WrittenPitch(step, 0, 4),
    )


def test_simultaneous_gesture_applies_explicit_score_chord_group():
    events = (
        event("n1", 1.000, 60),
        event("n2", 1.018, 64),
        event("n3", 1.029, 67),
    )
    candidate = piano_gesture_candidates(events)[0]

    projected = (
        score_note("n1", "C"),
        score_note("n2", "E"),
        score_note("n3", "G"),
    )
    grouped = apply_piano_gesture_candidate(candidate, projected)

    group_ids = {x.simultaneity_group_id for x in grouped}
    assert len(group_ids) == 1
    assert None not in group_ids


def test_arpeggiated_gesture_does_not_create_musicxml_chord_group():
    events = (
        event("n1", 1.000, 48, ("rolled",)),
        event("n2", 1.045, 55, ("rolled",)),
        event("n3", 1.082, 64, ("rolled",)),
    )
    candidate = piano_gesture_candidates(events)[0]

    projected = (
        score_note("n1", "C"),
        score_note("n2", "G"),
        score_note("n3", "E"),
    )
    result = apply_piano_gesture_candidate(candidate, projected)

    assert all(x.simultaneity_group_id is None for x in result)
    assert "arpeggiate" in result[0].markings
