from realtime.ensemble_app.stage1_quartet import Stage1QuartetRuntime


def test_latest_main_quartet_runtime_one_tick_smoke():
    runtime=Stage1QuartetRuntime.create(tempo_bpm=172.0)
    result=runtime.decide(
        "Cm7",
        "F7",
        beat_in_bar=0.0,
        bar_index=0,
        total_bars=32,
        tempo_bpm=172.0,
        section="A",
        chorus=0,
        song_id="Runtime Smoke",
    )
    assert result.state.transport.bar==0
    assert result.state.transport.beat==0.0
    assert result.decisions
