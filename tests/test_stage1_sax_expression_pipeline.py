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
