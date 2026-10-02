from realtime.ensemble_app.harmony_display import transpose_chord


def test_transpose_chord_root_and_quality():
    assert transpose_chord("Dm7", 2) == "Em7"
    assert transpose_chord("G7", -2) == "F7"


def test_transpose_slash_chord():
    assert transpose_chord("Cmaj7/E", 2) == "Dmaj7/F#"


def test_non_chord_markers_are_preserved():
    assert transpose_chord("N.C.", 5) == "N.C."
    assert transpose_chord("%", 5) == "%"
