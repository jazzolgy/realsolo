from realtime.ensemble_app.player_contract import (
    RenderGesture,
    RenderVoice,
    apply_shared_groove_to_render_gesture,
)
from realtime.ensemble_app.stage1_trio import Stage1TrioRuntime
from music_intelligence.reasoning.groove_context import (
    GrooveFeel,
    build_groove_context,
    groove_timing_offset_beats,
)


def test_stage1_preperformance_initializes_one_shared_swing_context():
    trio=Stage1TrioRuntime.create(tempo_bpm=120.0)
    assert trio.state.groove is not None
    assert trio.state.groove.feel is GrooveFeel.SWING
    assert trio.state.groove.grammar_id=="swing.eighth_triplet_feel"
    assert trio.state.groove.tempo_bpm==120.0


def test_renderer_projects_all_roles_to_same_swing_offbeat():
    groove=build_groove_context(GrooveFeel.SWING,tempo_bpm=120.0)
    expected=groove_timing_offset_beats(0.5,groove)
    assert expected>0

    for role in ("piano","bass","drums","tenor_sax"):
        voice=RenderVoice(
            60,
            onset_offset_beats=0.5,
            instrument_role=role,
        )
        gesture=(
            RenderGesture(role=role,drum_hits=(voice,))
            if role=="drums"
            else RenderGesture(role=role,voices=(voice,))
        )
        out=apply_shared_groove_to_render_gesture(
            gesture,
            anchor_beat=0.0,
            groove=groove,
        )
        rendered=(out.drum_hits or out.voices)[0]
        assert abs(rendered.onset_offset_beats-(0.5+expected))<1e-9
        assert out.annotations["groove_feel"]=="swing"
        assert "groove:swing" in out.tags


def test_stage1_runtime_attaches_same_groove_to_committed_player_gestures():
    trio=Stage1TrioRuntime.create(tempo_bpm=120.0)
    result=trio.decide(
        "Cmaj7",
        "Dm7",
        beat_in_bar=0.0,
        bar_index=0,
        total_bars=8,
        tempo_bpm=120.0,
        section="A",
    )
    assert result.state.groove is not None
    assert result.state.groove.feel is GrooveFeel.SWING
    assert result.gestures
    assert all(g.annotations.get("groove_feel")=="swing" for g in result.gestures)
    assert all("groove:swing" in g.tags for g in result.gestures)


def test_tempo_change_refreshes_shared_swing_ratio_for_every_player():
    trio=Stage1TrioRuntime.create(tempo_bpm=80.0)
    slow=trio.state.groove.swing_offbeat_fraction
    trio.decide(
        "Cmaj7",
        "",
        beat_in_bar=0.0,
        bar_index=0,
        total_bars=8,
        tempo_bpm=280.0,
    )
    fast=trio.state.groove.swing_offbeat_fraction
    assert slow>fast>0.5
