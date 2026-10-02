from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    PerformedPitch,
    PerformanceTimeSpan,
    UnpitchedToken,
)
from music_intelligence.transcribe.instrument_rules import (
    NoteheadStyle,
    bass_notation_directive,
    drum_notation_directive,
    sax_notation_directive,
)
from music_intelligence.transcribe.notation import NotationRelevance


def pitched(event_id, instrument, midi, technique=(), ornament=()):
    return CommittedPerformanceEvent(
        event_id=event_id,
        player_id=instrument,
        instrument=instrument,
        commitment=CommitmentState.COMMITTED,
        time=PerformanceTimeSpan(1.0, 1.4),
        pitch=PerformedPitch(nominal_midi=midi),
        technique=technique,
        ornament=ornament,
    )


def test_bass_dead_note_is_x_notehead_not_fake_pitch_policy():
    d = bass_notation_directive(
        pitched("bass:1", "upright_bass", 40, ("dead_note",))
    )
    assert d.notehead is NoteheadStyle.X
    assert d.relevance is NotationRelevance.INCLUDE


def test_bass_ghost_note_remains_optional_and_parenthesized():
    d = bass_notation_directive(
        pitched("bass:2", "electric_bass", 43, ("ghost_note",))
    )
    assert d.relevance is NotationRelevance.OPTIONAL
    assert d.parenthesized is True


def test_sax_scoop_is_expression_marking_not_invented_grace_note():
    d = sax_notation_directive(
        pitched("sax:1", "tenor_sax", 67, ("scoop",))
    )
    assert "scoop" in d.markings
    assert "grace-note" not in d.markings


def test_explicit_sax_grace_note_evidence_can_be_retained():
    d = sax_notation_directive(
        pitched("sax:2", "alto_sax", 72, (), ("grace_note",))
    )
    assert "grace-note" in d.markings


def test_cymbal_uses_x_notehead_and_drum_ghost_is_parenthesized():
    event = CommittedPerformanceEvent(
        event_id="drums:1",
        player_id="drums",
        instrument="drum_set",
        commitment=CommitmentState.PLAYED,
        time=PerformanceTimeSpan(1.0, 1.2),
        unpitched=UnpitchedToken("ride_cymbal", technique="ghost"),
        technique=("ghost_note",),
    )
    d = drum_notation_directive(event)
    assert d.notehead is NoteheadStyle.X
    assert d.parenthesized
