from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    PlayerPresence,
    PlayerRole,
    TransportState,
)
from music_intelligence.reasoning.interaction_scheduler import schedule_player

from realtime.ensemble_app.player_contract import RenderGesture, RenderVoice
from realtime.ensemble_app.trio_adapters import (
    BassRuntimeAdapter,
    DrumsRuntimeAdapter,
    NativeImmediateResult,
    PianoRuntimeAdapter,
    trio_adapter_status,
)


def snapshot():
    return EnsembleState(
        transport=TransportState(beat=1.0, bar=0),
        players=(
            PlayerPresence("piano", "piano", PlayerRole.COMPER),
            PlayerPresence("bass", "bass", PlayerRole.BASS),
            PlayerPresence("drums", "drums", PlayerRole.DRUMS),
        ),
    )


def decider_for(role, pitch):
    def decide(context):
        assert context["interaction_directive"].player_id == role
        gesture = RenderGesture(
            role=role,
            voices=(
                RenderVoice(pitch, duration_beats=.5, instrument_role=role),
            ) if role != "drums" else (),
            drum_hits=(
                RenderVoice(51, duration_beats=.1, instrument_role="drums"),
            ) if role == "drums" else (),
            source=f"native:{role}",
        )
        return NativeImmediateResult(
            gesture=gesture,
            density=.5,
            energy=.5,
            tension=.4,
            tags=frozenset({"native_decision"}),
        )
    return decide


def test_piano_adapter_converts_native_result_to_runtime_decision():
    s = snapshot()
    adapter = PianoRuntimeAdapter(decider_for("piano", 60))
    d = schedule_player(s, "piano")
    out = adapter.decide_immediate(snapshot=s, directive=d, context={})
    assert out.player_id == "piano"
    assert out.intent.player_id == "piano"
    assert out.gestures[0].source == "native:piano"


def test_all_trio_adapters_share_same_boundary_shape():
    s = snapshot()
    adapters = (
        PianoRuntimeAdapter(decider_for("piano", 60)),
        BassRuntimeAdapter(decider_for("bass", 36)),
        DrumsRuntimeAdapter(decider_for("drums", 0)),
    )
    for adapter in adapters:
        d = schedule_player(s, adapter.player_id)
        out = adapter.decide_immediate(snapshot=s, directive=d, context={})
        assert out is not None
        assert out.player_id == adapter.player_id
        assert out.intent.commitment.value == "committed"


def test_unconnected_native_player_returns_none_instead_of_fake_music():
    s = snapshot()
    adapter = BassRuntimeAdapter()
    d = schedule_player(s, "bass")
    assert adapter.decide_immediate(snapshot=s, directive=d, context={}) is None


def test_directive_adjusts_native_density_and_energy():
    s = snapshot()
    adapter = PianoRuntimeAdapter(decider_for("piano", 60))
    d = schedule_player(s, "piano")
    out = adapter.decide_immediate(snapshot=s, directive=d, context={})
    expected_density = max(0.0, min(1.0, .5 + d.density_delta))
    expected_energy = max(0.0, min(1.0, .5 + d.energy_delta))
    assert out.intent.density == expected_density
    assert out.intent.energy == expected_energy


def test_status_distinguishes_adapter_from_connected_native_player():
    status = trio_adapter_status(
        PianoRuntimeAdapter(decider_for("piano", 60)),
        BassRuntimeAdapter(),
        DrumsRuntimeAdapter(),
    )
    by_id = {x.player_id: x for x in status}
    assert by_id["piano"].adapter_ready is True
    assert by_id["piano"].native_decider_connected is True
    assert by_id["bass"].adapter_ready is True
    assert by_id["bass"].native_decider_connected is False
