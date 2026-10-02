from xml.etree import ElementTree as ET
from fractions import Fraction

from music_intelligence.transcribe.instrument_profiles import (
    resolve_instrument_profile,
    written_range_warning,
)
from music_intelligence.transcribe.musicxml import score_to_musicxml
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import ScoreEvent, ScorePart, assemble_score
from music_intelligence.transcribe.spelling import WrittenPitch


def note(part_id, staff_id, pitch):
    return ScoreEvent(
        event_id=f"{part_id}:1",
        part_id=part_id,
        staff_id=staff_id,
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1)),
        source_event_ids=(f"src:{part_id}",),
        written_pitch=pitch,
    )


def test_classical_profiles_resolve_common_clefs_and_transpositions():
    viola = resolve_instrument_profile("viola")
    clarinet = resolve_instrument_profile("clarinet")
    horn = resolve_instrument_profile("french_horn")
    piano = resolve_instrument_profile("piano")

    assert viola.clefs[0].sign == "C"
    assert viola.clefs[0].line == 3
    assert clarinet.transposition.chromatic_semitones == -2
    assert horn.transposition.chromatic_semitones == -7
    assert piano.staff_count == 2


def test_musicxml_emits_piano_two_clefs():
    upper = note("piano", "upper", WrittenPitch("C", 0, 5))
    part = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("upper", "lower"),
        (upper,),
        profile_id="piano",
    )
    score = assemble_score(score_id="profile:piano", title="Piano", parts=(part,))
    root = ET.fromstring(score_to_musicxml(score))

    clefs = root.findall(".//attributes/clef")
    assert len(clefs) == 2
    assert clefs[0].findtext("sign") == "G"
    assert clefs[1].findtext("sign") == "F"


def test_musicxml_emits_bb_clarinet_transposition_and_treble_clef():
    event = note("cl", "staff", WrittenPitch("C", 0, 5))
    part = ScorePart(
        "cl",
        "Clarinet in Bb",
        "clarinet_bb",
        ("staff",),
        (event,),
        profile_id="clarinet_bb",
    )
    score = assemble_score(score_id="profile:cl", title="Clarinet", parts=(part,))
    root = ET.fromstring(score_to_musicxml(score))

    assert root.findtext(".//attributes/clef/sign") == "G"
    assert root.findtext(".//attributes/transpose/chromatic") == "-2"
    assert root.findtext(".//attributes/transpose/diatonic") == "-1"


def test_written_range_warning_is_advisory_only():
    violin = resolve_instrument_profile("violin")

    assert written_range_warning(violin, 40) == "below advisory written range"
    assert written_range_warning(violin, 60) is None
