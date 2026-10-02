from fractions import Fraction
from xml.etree import ElementTree as ET

from music_intelligence.transcribe.musicxml import score_to_musicxml
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import ScoreEvent, ScorePart, assemble_score
from music_intelligence.transcribe.spelling import WrittenPitch


def _note(event_id, step, onset, duration, group=None, dynamic=None):
    return ScoreEvent(
        event_id=event_id,
        part_id="piano",
        staff_id="upper",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(onset), Fraction(duration)),
        source_event_ids=(f"src:{event_id}",),
        written_pitch=WrittenPitch(step, 0, 4),
        simultaneity_group_id=group,
        dynamic_marking=dynamic,
    )


def test_musicxml_emits_chord_elements_for_simultaneous_triad():
    events = (
        _note("c", "C", 0, 1, "triad:1", "mf"),
        _note("e", "E", 0, 1, "triad:1", "mf"),
        _note("g", "G", 0, 1, "triad:1", "mf"),
        _note("next", "A", 1, 1),
    )
    part = ScorePart("piano", "Piano", "piano", ("upper", "lower"), events)
    score = assemble_score(score_id="chord", title="Chord", parts=(part,))

    root = ET.fromstring(score_to_musicxml(score))
    notes = root.findall(".//part[@id='piano']/measure/note")

    assert notes[0].find("chord") is None
    assert notes[1].find("chord") is not None
    assert notes[2].find("chord") is not None
    assert notes[3].find("chord") is None
    assert [n.findtext("pitch/step") for n in notes] == ["C", "E", "G", "A"]
    assert len(root.findall(".//direction/direction-type/dynamics/mf")) == 1


def test_separate_same_voice_onsets_do_not_become_chord_without_group():
    events = (
        _note("c", "C", 0, 1),
        _note("e", "E", 1, 1),
        _note("g", "G", 2, 1),
    )
    part = ScorePart("piano", "Piano", "piano", ("upper", "lower"), events)
    score = assemble_score(score_id="line", title="Line", parts=(part,))

    root = ET.fromstring(score_to_musicxml(score))

    assert root.findall(".//note/chord") == []
