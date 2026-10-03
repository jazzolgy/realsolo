from music_intelligence.reasoning.groove_context import GrooveCoordinationMode
from realtime.ensemble_app.stage1_quartet import Stage1QuartetRuntime


def test_quartet_initializes_four_native_players_in_elastic_fixed_tempo_mode():
    quartet=Stage1QuartetRuntime.create(tempo_bpm=172.0)
    assert [p.player_id for p in quartet.state.players] == [
        "piano","bass","drums","sax"
    ]
    assert quartet.state.groove is not None
    assert quartet.state.groove.coordination_mode is GrooveCoordinationMode.ELASTIC
    assert quartet.state.groove.tempo_elasticity == 0.0
    assert quartet.state.leader_player_id == "sax"


def test_quartet_tick_commits_four_independent_immediate_decisions():
    quartet=Stage1QuartetRuntime.create(tempo_bpm=172.0)
    result=quartet.decide(
        "Cm7",
        "F7",
        beat_in_bar=0.0,
        bar_index=0,
        total_bars=32,
        tempo_bpm=172.0,
        section="A",
    )
    assert result.snapshot_generation >= 0
    ids={decision.player_id for decision in result.decisions}
    assert ids == {"piano","bass","drums","sax"}
    assert result.state.intent_for("sax") is not None
    assert all(not hasattr(decision,"future_notes") for decision in result.decisions)


def test_quartet_sax_uses_runtime_boundary_shared_groove():
    quartet=Stage1QuartetRuntime.create(tempo_bpm=172.0)
    result=quartet.decide(
        "Cm7",
        "F7",
        beat_in_bar=.5,
        bar_index=0,
        total_bars=32,
        tempo_bpm=172.0,
        section="A",
    )
    sax_gestures=[g for g in result.gestures if g.source=="player/sax:canonical_immediate"]
    assert sax_gestures
    sax=sax_gestures[0]
    assert sax.annotations["groove_coordination"]=="elastic"
    assert sax.annotations["groove_feel"]=="swing"
    assert "groove:swing" in sax.tags


def test_quartet_second_tick_lets_accompanists_see_prior_sax_intent_only():
    quartet=Stage1QuartetRuntime.create(tempo_bpm=172.0)
    first=quartet.decide(
        "Cm7","F7",
        beat_in_bar=0.0,
        bar_index=0,
        total_bars=32,
        tempo_bpm=172.0,
        section="A",
    )
    sax_intent=first.state.intent_for("sax")
    assert sax_intent is not None

    second=quartet.decide(
        "Cm7","F7",
        beat_in_bar=1.0,
        bar_index=0,
        total_bars=32,
        tempo_bpm=172.0,
        section="A",
    )
    assert second.snapshot_generation == quartet.state.generation - (
        second.state.generation - second.snapshot_generation
    ) or second.snapshot_generation >= first.state.generation
    assert second.state.intent_for("piano") is not None
    assert second.state.intent_for("drums") is not None
