from realtime.ensemble_app.player_contract import monophonic_solo_gesture
from realtime.ensemble_app.stage1_music import Stage1Soloist


def test_stage1_solo_adds_expression_after_note_selection():
    solo = Stage1Soloist()
    first = solo.choose("Dm7", "G7", beat_in_bar=0.0, phrase_step=0)
    second = solo.choose("Dm7", "G7", beat_in_bar=1.0, phrase_step=1)

    assert first["pitch"] is not None
    assert second["pitch"] is not None
    assert isinstance(second["articulation"], list)
    assert second["velocity"] >= 1


def test_render_gesture_carries_tenor_sax_expression():
    gesture = monophonic_solo_gesture(
        62,
        1.0,
        velocity=76,
        articulation=("vibrato", "fall"),
        instrument_role="tenor_sax",
    ).to_dict()

    voice = gesture["voices"][0]
    assert voice["pitch_midi"] == 62
    assert voice["instrument_role"] == "tenor_sax"
    assert voice["articulation"] == ["vibrato", "fall"]


def test_phrase_hints_are_serialized_for_renderer():
    gesture = monophonic_solo_gesture(
        64,
        .5,
        articulation=("legato",),
        instrument_role="tenor_sax",
        breath_before_beats=.18,
        attack_scale=.55,
        release_shape="connected",
    ).to_dict()
    voice = gesture["voices"][0]
    assert voice["breath_before_beats"] == .18
    assert voice["attack_scale"] == .55
    assert voice["release_shape"] == "connected"


def test_solo_reset_clears_phrase_memory():
    solo = Stage1Soloist()
    for step in range(4):
        solo.choose("Dm7", "G7", beat_in_bar=float(step % 4), phrase_step=step)
    assert solo.phrase_memory.notes_since_breath > 0
    solo.reset()
    assert solo.phrase_memory.notes_since_breath == 0
    assert solo.phrase_memory.beats_since_breath == 0.0


def test_stage1_solo_exposes_causal_articulation_arc():
    solo = Stage1Soloist()
    event = solo.choose("Dm7", "G7", beat_in_bar=0.0, phrase_step=0)
    assert event["arc_phase"] in {"attack", "body", "peak", "release"}
    assert 0.2 <= event["attack_scale"] <= 1.5
    assert isinstance(event["arc_reasons"], list)
