from realtime.ensemble_app.stage1_quartet import Stage1QuartetRuntime


def _tick(runtime, beat):
    return runtime.decide(
        "Cm7",
        "F7",
        beat_in_bar=beat,
        bar_index=0,
        total_bars=32,
        tempo_bpm=172.0,
        section="A",
    )


def test_walking_bass_uses_quarter_spine_and_offbeat_ghost_path():
    quartet=Stage1QuartetRuntime.create(172.0)
    down=_tick(quartet,0.0)
    bass_down=next(d for d in down.decisions if d.player_id=="bass")
    assert "player/bass:sequential_runner" in bass_down.intent.provenance

    off=_tick(quartet,.5)
    bass_off=next(d for d in off.decisions if d.player_id=="bass")
    assert any(tag in bass_off.intent.tags for tag in {
        "bass_ghost_note","bass_ghost_space","eighth_offbeat"
    })
    assert "player/bass:sequential_runner" not in {
        g.source for g in bass_off.gestures
    }


def test_sax_runtime_exposes_shared_solo_and_motif_decisions():
    quartet=Stage1QuartetRuntime.create(172.0)
    result=_tick(quartet,0.0)
    sax_gesture=next(
        g for g in result.gestures
        if g.source=="player/sax:canonical_immediate"
    )
    assert sax_gesture.annotations["shared_solo_method"]
    assert sax_gesture.annotations["shared_entry_mode"]
    assert sax_gesture.annotations["shared_target_mode"]
    assert sax_gesture.annotations["motif_id"]
    sax_decision=next(d for d in result.decisions if d.player_id=="sax")
    assert "shared_solo_runtime" in sax_decision.intent.provenance
    assert "shared_motif_policy" in sax_decision.intent.provenance


def test_bebop_quartet_uses_bebop_drum_runtime_not_generic_only():
    quartet=Stage1QuartetRuntime.create(172.0)
    result=_tick(quartet,0.0)
    drums=next(d for d in result.decisions if d.player_id=="drums")
    assert "drummer_bebop_runtime" in drums.intent.provenance


def test_piano_receives_shared_harmonic_reasoning_path():
    quartet=Stage1QuartetRuntime.create(172.0)
    first=_tick(quartet,0.0)
    assert next(d for d in first.decisions if d.player_id=="piano") is not None
    second=_tick(quartet,.5)
    piano=next(d for d in second.decisions if d.player_id=="piano")
    # The exact comping gesture may be silence; the decision must still come
    # through the canonical piano comping policy after shared-context wiring.
    assert "piano_comping_policy" in piano.intent.provenance
