from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    PlayerPresence,
    PlayerRole,
    TransportState,
)
from music_intelligence.reasoning.interaction_scheduler import schedule_player

from realtime.ensemble_app.native_trio_players import (
    Stage1BassNativeDecider,
    Stage1DrumsNativeDecider,
    Stage1PianoNativeDecider,
)
from realtime.ensemble_app.trio_adapters import (
    BassRuntimeAdapter,
    DrumsRuntimeAdapter,
    PianoRuntimeAdapter,
)
from realtime.ensemble_app.runtime_loop import EnsembleRuntimeLoop


def trio_state():
    return EnsembleState(
        transport=TransportState(
            beat=1.0,
            bar=0,
            section="A",
            tempo_bpm=140.0,
            form_position=.2,
        ),
        players=(
            PlayerPresence("piano", "piano", PlayerRole.COMPER),
            PlayerPresence("bass", "bass", PlayerRole.BASS),
            PlayerPresence("drums", "drums", PlayerRole.DRUMS),
        ),
    )


def runtime_context():
    return {
        "chord_symbol": "Dm7",
        "next_chord": "G7",
        "beat_in_bar": 1.0,
        "bar_index": 0,
        "beats_per_bar": 4,
        "tempo_bpm": 140.0,
        "phrase_position": .4,
    }


def test_native_bass_decider_returns_real_player_gesture():
    s = trio_state()
    adapter = BassRuntimeAdapter(Stage1BassNativeDecider())
    d = schedule_player(s, "bass")
    out = adapter.decide_immediate(snapshot=s, directive=d, context=runtime_context())
    assert out is not None
    assert out.gestures
    assert out.gestures[0].source == "player/bass:immediate_realizer"
    assert out.gestures[0].voices


def test_native_drum_decider_returns_online_drummer_gesture():
    s = trio_state()
    adapter = DrumsRuntimeAdapter(Stage1DrumsNativeDecider())
    d = schedule_player(s, "drums")
    out = adapter.decide_immediate(snapshot=s, directive=d, context=runtime_context())
    assert out is not None
    assert out.gestures
    assert out.gestures[0].source == "player/drums:online_drummer"


def test_native_piano_decider_wraps_existing_stage1_player():
    s = trio_state()
    adapter = PianoRuntimeAdapter(Stage1PianoNativeDecider())
    d = schedule_player(s, "piano")
    out = adapter.decide_immediate(snapshot=s, directive=d, context=runtime_context())
    assert out is not None
    assert out.intent.player_id == "piano"


def test_full_trio_runtime_cycle_uses_native_deciders():
    loop = EnsembleRuntimeLoop((
        PianoRuntimeAdapter(Stage1PianoNativeDecider()),
        BassRuntimeAdapter(Stage1BassNativeDecider()),
        DrumsRuntimeAdapter(Stage1DrumsNativeDecider()),
    ))
    result = loop.step(trio_state(), context=runtime_context())
    assert {x.player_id for x in result.decisions} == {"piano", "bass", "drums"}
    assert result.skipped_player_ids == ()
    sources = {g.source for g in result.gestures}
    assert "player/bass:immediate_realizer" in sources
    assert "player/drums:online_drummer" in sources
