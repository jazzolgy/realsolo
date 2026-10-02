from realtime.ensemble_app.stage1_trio import Stage1TrioRuntime


def test_stage1_native_trio_returns_piano_bass_and_drums_decisions():
    trio = Stage1TrioRuntime.create(120.0)
    result = trio.decide(
        "G7",
        "Cmaj7",
        beat_in_bar=0.0,
        bar_index=1,
        total_bars=8,
        tempo_bpm=120.0,
        section="A",
        chorus=0,
    )
    ids = {d.player_id for d in result.decisions}
    assert {"piano", "bass", "drums"} <= ids
    roles = {g.role for g in result.gestures}
    assert "bass" in roles
    assert "drums" in roles
    # Piano may intentionally choose silence; its committed decision must still exist.
    assert "piano" in ids


def test_stage1_native_trio_keeps_single_immediate_cycle():
    trio = Stage1TrioRuntime.create()
    first = trio.decide(
        "Dm7", "G7",
        beat_in_bar=0.0, bar_index=0, total_bars=8, tempo_bpm=120.0,
    )
    second = trio.decide(
        "Dm7", "G7",
        beat_in_bar=1.0, bar_index=0, total_bars=8, tempo_bpm=120.0,
    )
    assert second.snapshot_generation >= first.snapshot_generation
    assert all(not hasattr(d, "future_bar") for d in second.decisions)
