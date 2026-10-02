from music_intelligence.reasoning.groove_context import (
    GrooveCoordinationMode,
    GrooveFeel,
    build_groove_context,
)
from realtime.ensemble_app.player_contract import (
    RenderGesture,
    RenderVoice,
    apply_shared_groove_to_render_gesture,
)
from realtime.ensemble_app.stage1_trio import Stage1TrioRuntime


def _gesture(role: str) -> RenderGesture:
    return RenderGesture(
        role=role,
        voices=(RenderVoice(60,onset_offset_beats=.5,instrument_role=role),),
    )


def test_locked_mode_keeps_players_on_identical_shared_swing_reference():
    groove=build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=120.0,
        coordination_mode=GrooveCoordinationMode.LOCKED,
        phase_elasticity=0.0,
        swing_elasticity=0.0,
    )
    values=[]
    for role in ("piano","bass","tenor_sax"):
        out=apply_shared_groove_to_render_gesture(
            _gesture(role),
            anchor_beat=0.0,
            groove=groove,
            phrase_maturity=.5,
        )
        values.append(out.voices[0].onset_offset_beats)
    assert max(values)-min(values) < 1e-12


def test_elastic_mode_keeps_groove_but_separates_player_placement():
    groove=build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=120.0,
        coordination_mode=GrooveCoordinationMode.ELASTIC,
        phase_elasticity=.8,
        swing_elasticity=.8,
    )
    offsets={}
    for role in ("piano","bass","tenor_sax"):
        out=apply_shared_groove_to_render_gesture(
            _gesture(role),
            anchor_beat=0.0,
            groove=groove,
            phrase_maturity=.5,
        )
        offsets[role]=out.voices[0].onset_offset_beats
        assert out.annotations["groove_coordination_mode"]=="elastic"
    assert len({round(v,6) for v in offsets.values()})==3
    assert all(.5 < v < .8 for v in offsets.values())


def test_stage1_defaults_to_elastic_not_robotic_locked_mode():
    trio=Stage1TrioRuntime.create(tempo_bpm=130.0)
    assert trio.state.groove.coordination_mode is GrooveCoordinationMode.ELASTIC


def test_human_drift_changes_transport_tempo_slowly_not_abruptly():
    trio=Stage1TrioRuntime.create(
        tempo_bpm=120.0,
        coordination_mode=GrooveCoordinationMode.HUMAN_DRIFT,
    )
    initial=trio.state.transport.tempo_bpm
    for beat in range(4):
        trio.decide(
            "Cmaj7","Dm7",
            beat_in_bar=float(beat),
            bar_index=0,
            total_bars=8,
            tempo_bpm=120.0,
            coordination_mode=GrooveCoordinationMode.HUMAN_DRIFT,
        )
    current=trio.state.transport.tempo_bpm
    assert abs(current-initial) < 2.0
    assert trio.state.groove.coordination_mode is GrooveCoordinationMode.HUMAN_DRIFT


def test_switching_to_locked_resets_player_phase_elasticity():
    trio=Stage1TrioRuntime.create(
        tempo_bpm=120.0,
        coordination_mode=GrooveCoordinationMode.ELASTIC,
    )
    trio.decide(
        "Cmaj7","Dm7",
        beat_in_bar=0.0,
        bar_index=0,
        total_bars=8,
        tempo_bpm=120.0,
        coordination_mode=GrooveCoordinationMode.LOCKED,
    )
    assert trio.state.groove.coordination_mode is GrooveCoordinationMode.LOCKED
    assert trio.state.groove.phase_elasticity==0.0
    assert trio.state.groove.swing_elasticity==0.0
