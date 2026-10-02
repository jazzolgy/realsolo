from realtime.ensemble_app.stage1_trio import Stage1TrioRuntime
from realtime.ensemble_app.rehearsal import run_chart_rehearsal


def test_stage1_runtime_can_promote_bass_to_soloist_role():
    runtime = Stage1TrioRuntime.create(140.0)
    result = runtime.decide(
        "Dm7",
        "G7",
        beat_in_bar=0.0,
        bar_index=0,
        total_bars=4,
        tempo_bpm=140.0,
        bass_solo=True,
    )
    bass_presence = next(p for p in result.state.players if p.player_id == "bass")
    assert bass_presence.role.value == "soloist"

    bass_decision = next(d for d in result.decisions if d.player_id == "bass")
    assert bass_decision.intent.leadership >= .55
    assert "solo" in bass_decision.intent.tags


def test_bass_solo_gesture_exposes_solo_method_annotation_when_pitched():
    runtime = Stage1TrioRuntime.create(140.0)
    result = runtime.decide(
        "Dm7",
        "G7",
        beat_in_bar=.5,
        bar_index=1,
        total_bars=4,
        tempo_bpm=140.0,
        bass_solo=True,
    )
    bass_gestures = [g for g in result.gestures if g.role == "bass"]
    if bass_gestures:
        ann = bass_gestures[0].annotations
        assert ann["bass_mode"] == "solo"
        assert ann["solo_operation"]
        assert ann["solo_family"]


def test_half_beat_rehearsal_ticks_enable_solo_subdivision_decisions():
    runtime = Stage1TrioRuntime.create(132.0)
    log = run_chart_rehearsal(
        runtime,
        ("Dm7", "G7", "Cmaj7", "Cmaj7"),
        tempo_bpm=132.0,
        bass_solo=True,
        subdivisions_per_beat=2,
    )
    assert len(log.ticks) == 4 * 4 * 2
    assert any(abs(t.beat_in_bar % 1.0 - .5) < 1e-9 for t in log.ticks)


def test_active_space_does_not_remove_bass_from_runtime_decisions():
    runtime = Stage1TrioRuntime.create(126.0)
    seen_space = False
    for i in range(24):
        beat = (i * .5) % 4.0
        bar = i // 8
        result = runtime.decide(
            "Dm7" if bar % 2 == 0 else "G7",
            "G7" if bar % 2 == 0 else "Cmaj7",
            beat_in_bar=beat,
            bar_index=bar,
            total_bars=6,
            tempo_bpm=126.0,
            bass_solo=True,
        )
        bass = next((d for d in result.decisions if d.player_id == "bass"), None)
        assert bass is not None
        if "bass_space" in bass.intent.tags:
            seen_space = True
            assert bass.gestures == ()
    assert seen_space is True
