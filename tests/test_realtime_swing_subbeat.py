from realtime.ensemble_app.stage1_trio import Stage1TrioRuntime
from realtime.ensemble_app.stage1_web import groove_payload


def test_shared_groove_endpoint_uses_tempo_conditioned_swing():
    slow=groove_payload(80.0)
    fast=groove_payload(280.0)
    assert slow["feel"]=="swing"
    assert slow["offbeat_fraction"]>fast["offbeat_fraction"]>0.5


def test_drum_only_substep_hits_shared_swing_offbeat():
    trio=Stage1TrioRuntime.create(tempo_bpm=120.0)
    # Establish the preceding beat first.
    trio.decide(
        "Cmaj7",
        "Dm7",
        beat_in_bar=1.0,
        bar_index=0,
        total_bars=8,
        tempo_bpm=120.0,
        section="A",
    )
    off=trio.state.groove.swing_offbeat_fraction
    sub=trio.decide(
        "Cmaj7",
        "Dm7",
        beat_in_bar=1.0+off,
        bar_index=0,
        total_bars=8,
        tempo_bpm=120.0,
        section="A",
        active_player_ids=frozenset({"drums"}),
    )
    assert {d.player_id for d in sub.decisions} <= {"drums"}
    assert sub.decisions
    assert sub.gestures
    assert all(g.role=="drums" for g in sub.gestures)
    assert all("groove:swing" in g.tags for g in sub.gestures)
    assert any(hit.pitch_midi==51 for g in sub.gestures for hit in g.drum_hits)


def test_full_tick_reactivates_all_players_after_drum_substep():
    trio=Stage1TrioRuntime.create(tempo_bpm=120.0)
    off=trio.state.groove.swing_offbeat_fraction
    trio.decide(
        "Cmaj7","Dm7",
        beat_in_bar=1.0+off,
        bar_index=0,total_bars=8,tempo_bpm=120.0,
        active_player_ids=frozenset({"drums"}),
    )
    full=trio.decide(
        "Cmaj7","Dm7",
        beat_in_bar=2.0,
        bar_index=0,total_bars=8,tempo_bpm=120.0,
    )
    assert {p.player_id for p in full.state.active_players()}=={"piano","bass","drums"}
