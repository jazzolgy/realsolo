from realtime.ensemble_app.stage1_piano import Stage1PianoPlayer


def test_stage1_piano_uses_real_player_pipeline_and_returns_immediate_gesture_or_silence():
    player = Stage1PianoPlayer.create()
    gesture = player.decide(
        "G7",
        "Cmaj7",
        beat_in_bar=3.0,
        bar_index=1,
    )
    assert len(player.state.committed) == 1
    if gesture is not None:
        assert gesture.role == "piano"
        assert gesture.source.startswith("piano_")
        assert all(v.instrument_role == "piano" for v in gesture.voices)


def test_stage1_piano_reset_clears_player_memory():
    player = Stage1PianoPlayer.create()
    player.decide("Dm7", "G7", beat_in_bar=1.0, bar_index=0)
    assert player.state.committed
    player.reset()
    assert not player.state.committed
