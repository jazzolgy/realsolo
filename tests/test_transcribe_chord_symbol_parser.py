from music_intelligence.transcribe import (
    EnharmonicPolicy,
    parse_chord_symbol,
)


def test_parser_preserves_open_ended_jazz_suffixes_and_slash_bass():
    chord = parse_chord_symbol("F#7alt/C#")

    assert chord.root_pc == 6
    assert chord.quality == "7alt"
    assert chord.bass_pc == 1
    assert chord.enharmonic_policy is EnharmonicPolicy.PREFER_SHARPS
    assert chord.display() == "F#7alt/C#"


def test_parser_handles_sus_half_diminished_style_and_no_chord():
    sus = parse_chord_symbol("Bb13sus4")
    half_dim = parse_chord_symbol("Dm7b5")
    nc = parse_chord_symbol("N.C.")

    assert sus.display() == "Bb13sus4"
    assert half_dim.display() == "Dm7b5"
    assert nc.display() == "N.C."


def test_transpose_can_choose_sharp_or_flat_spelling():
    chord = parse_chord_symbol("C7")

    sharp = chord.transpose(1, enharmonic_policy=EnharmonicPolicy.PREFER_SHARPS)
    flat = chord.transpose(1, enharmonic_policy=EnharmonicPolicy.PREFER_FLATS)

    assert sharp.display() == "C#7"
    assert flat.display() == "Db7"
