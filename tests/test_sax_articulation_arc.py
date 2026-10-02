from players.sax.arc import (
    SaxArcContext,
    apply_sax_arc,
    choose_sax_articulation_arc,
)


def test_phrase_attack_is_tongued_without_future_note_plan():
    d = choose_sax_articulation_arc(
        SaxArcContext(64, None, .5, .0, 0, True, True, False)
    )
    assert d.phase == "attack"
    assert "tongued" in d.add_articulations


def test_middle_stepwise_line_forms_slur_group():
    d = choose_sax_articulation_arc(
        SaxArcContext(65, 64, .5, .4, 2, False, False, False)
    )
    assert d.phase == "body"
    assert "legato" in d.add_articulations
    assert d.release_shape == "connected"


def test_every_fourth_note_can_rearticulate():
    d = choose_sax_articulation_arc(
        SaxArcContext(65, 64, .5, .4, 4, False, False, False)
    )
    assert "tongued" in d.add_articulations
    assert "legato" in d.remove_articulations


def test_rising_late_middle_arrival_can_be_peak():
    d = choose_sax_articulation_arc(
        SaxArcContext(72, 67, .75, .66, 5, False, False, False, .55)
    )
    assert d.phase == "peak"
    assert "accent" in d.add_articulations
    assert d.velocity_delta > 0


def test_phrase_release_reduces_attack_and_opens_tail():
    d = choose_sax_articulation_arc(
        SaxArcContext(69, 67, 1.0, .94, 6, False, False, True)
    )
    tags, velocity, attack, release = apply_sax_arc(
        ("accent", "vibrato"), 82, 1.0, "normal", d
    )
    assert "accent" not in tags
    assert velocity < 82
    assert release == "open"
