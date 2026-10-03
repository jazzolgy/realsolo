from realtime.ensemble_app.player_contract import (
    RenderGesture,
    RenderVoice,
    apply_shared_groove_to_render_gesture,
)
from realtime.ensemble_app.stage1_trio import Stage1TrioRuntime
from players.sax.solo_realizer import SaxSoloRealizerContext
from music_intelligence.reasoning.groove_context import (
    GrooveCoordinationMode,
    GrooveFeel,
    build_groove_context,
)


def test_stage1_preperformance_initializes_one_shared_swing_context():
    trio=Stage1TrioRuntime.create(tempo_bpm=120.0)
    assert trio.state.groove is not None
    assert trio.state.groove.feel is GrooveFeel.SWING
    assert trio.state.groove.grammar_id=="swing.eighth_triplet_feel"
    assert trio.state.groove.tempo_bpm==120.0


def _rendered_offbeat(role, groove, *, phrase_maturity=.5):
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
        phrase_maturity=phrase_maturity,
    )
    rendered=(out.drum_hits or out.voices)[0]
    return rendered.onset_offset_beats,out


def test_locked_renderer_projects_all_roles_to_same_swing_offbeat():
    groove=build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=120.0,
        coordination_mode=GrooveCoordinationMode.LOCKED,
    )
    positions=[]
    for role in ("piano","bass","drums","tenor_sax"):
        position,out=_rendered_offbeat(role,groove)
        positions.append(position)
        assert out.annotations["groove_coordination"]=="locked"
        assert "groove:swing" in out.tags
    assert max(positions)-min(positions)<1e-9


def test_elastic_renderer_keeps_shared_pulse_but_allows_bounded_role_placement():
    groove=build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=120.0,
        coordination_mode=GrooveCoordinationMode.ELASTIC,
    )
    positions={
        role:_rendered_offbeat(role,groove,phrase_maturity=.5)[0]
        for role in ("piano","bass","drums","tenor_sax")
    }
    assert len({round(x,8) for x in positions.values()})>1
    assert all(.55 < x < .8 for x in positions.values())
    assert positions["tenor_sax"] < positions["piano"]


def test_sax_realizer_does_not_own_shared_groove_projection():
    fields=set(SaxSoloRealizerContext.__dataclass_fields__)
    assert "groove" not in fields
    assert "beat_position_beats" not in fields

    groove=build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=120.0,
        coordination_mode=GrooveCoordinationMode.ELASTIC,
    )
    once,_=_rendered_offbeat("tenor_sax",groove)
    assert once != .5
    assert abs(once-.5) < .3


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
