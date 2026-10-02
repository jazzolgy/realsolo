from realtime.ensemble_app.stage1_trio import Stage1TrioRuntime


def test_stage1_bass_solo_can_select_scott_lafaro_legend_profile():
    runtime = Stage1TrioRuntime.create(132.0)
    result = runtime.decide(
        "Dm7",
        "G7",
        beat_in_bar=1.0,
        bar_index=1,
        total_bars=8,
        tempo_bpm=132.0,
        bass_solo=True,
        bass_legend="scott_lafaro",
    )
    bass = next(d for d in result.decisions if d.player_id == "bass")
    assert "scott_lafaro" in bass.intent.tags

    if bass.gestures:
        gesture = bass.gestures[0]
        assert gesture.annotations["bass_mode"] == "solo"
        assert gesture.annotations["legend_id"] == "scott_lafaro"
        assert gesture.annotations["solo_operation"]


def test_stage1_generic_bass_solo_has_no_legend_annotation():
    runtime = Stage1TrioRuntime.create(132.0)
    result = runtime.decide(
        "Dm7",
        "G7",
        beat_in_bar=1.0,
        bar_index=1,
        total_bars=8,
        tempo_bpm=132.0,
        bass_solo=True,
    )
    bass = next(d for d in result.decisions if d.player_id == "bass")
    if bass.gestures:
        assert bass.gestures[0].annotations["legend_id"] == ""
