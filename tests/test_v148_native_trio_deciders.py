from music_intelligence.harmony import HarmonicEvidence, HarmonicFrame, HarmonySource
from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    PlayerPresence,
    PlayerRole,
    TransportState,
)

from players.piano import PianoVoicingRequest, ResolvedHarmonicMaterial
from realtime.ensemble_app.native_deciders import (
    BassNativeDecider,
    DrumsNativeDecider,
    PianoNativeDecider,
    build_native_trio_runtime,
)
from realtime.ensemble_app.runtime_loop import EnsembleRuntimeLoop
from realtime.ensemble_app.trio_adapters import (
    BassRuntimeAdapter,
    DrumsRuntimeAdapter,
    PianoRuntimeAdapter,
)


def frame():
    return HarmonicFrame(
        expected=HarmonicEvidence(
            HarmonySource.EXPECTED,
            symbol="G7",
            root_pc=7,
            pitch_classes=frozenset({7, 11, 2, 5}),
            function="dominant",
        ),
        next_expected=HarmonicEvidence(
            HarmonySource.EXPECTED,
            symbol="Cmaj7",
            root_pc=0,
            pitch_classes=frozenset({0, 4, 7, 11}),
            function="tonic",
        ),
        tension=.65,
    )


def state():
    return EnsembleState(
        transport=TransportState(
            beat=0.0,
            bar=0,
            section="A",
            tempo_bpm=140.0,
            meter_numerator=4,
            meter_denominator=4,
            form_position=.2,
        ),
        players=(
            PlayerPresence("piano", "piano", PlayerRole.COMPER),
            PlayerPresence("bass", "bass", PlayerRole.BASS),
            PlayerPresence("drums", "drums", PlayerRole.DRUMS),
        ),
    )


def piano_request():
    return PianoVoicingRequest(
        ResolvedHarmonicMaterial(
            affordance_id="test.g7",
            role_pitch_classes={
                "root": (7,),
                "3rd": (11,),
                "7th": (5,),
                "9th": (9,),
            },
            root_pitch_class=7,
        ),
        bassist_present=True,
        duration_beats=.5,
    )


def test_bass_native_decider_uses_real_immediate_realizer():
    decider = BassNativeDecider()
    out = decider({
        "ensemble_snapshot": state(),
        "interaction_directive": __import__(
            "music_intelligence.reasoning.interaction_scheduler",
            fromlist=["schedule_player"],
        ).schedule_player(state(), "bass"),
        "harmonic_frame": frame(),
    })
    assert out is not None
    assert out.gesture is not None
    assert out.gesture.source == "player/bass:immediate_realizer"
    assert len(out.gesture.voices) == 1


def test_drums_native_decider_uses_real_online_drummer():
    from music_intelligence.reasoning.interaction_scheduler import schedule_player
    s = state()
    decider = DrumsNativeDecider()
    out = decider({
        "ensemble_snapshot": s,
        "interaction_directive": schedule_player(s, "drums"),
        "harmonic_frame": frame(),
    })
    assert out is not None
    assert out.gesture is not None
    assert out.gesture.source == "player/drums:online_drummer"


def test_piano_native_decider_uses_existing_comping_pipeline():
    from music_intelligence.reasoning.interaction_scheduler import schedule_player
    s = state()
    decider = PianoNativeDecider()
    out = decider({
        "ensemble_snapshot": s,
        "interaction_directive": schedule_player(s, "piano"),
        "harmonic_frame": frame(),
        "piano_voicing_request": piano_request(),
    })
    assert out is not None
    # Silence is a valid comping decision; if sounding, it must come from policy.
    if out.gesture is not None:
        assert out.gesture.source == "player/piano:comping_policy"


def test_real_native_deciders_run_together_in_runtime_loop():
    loop = EnsembleRuntimeLoop((
        PianoRuntimeAdapter(PianoNativeDecider()),
        BassRuntimeAdapter(BassNativeDecider()),
        DrumsRuntimeAdapter(DrumsNativeDecider()),
    ))
    result = loop.step(
        state(),
        context={
            "harmonic_frame": frame(),
            "piano_voicing_request": piano_request(),
        },
    )
    assert {x.player_id for x in result.decisions} == {"piano", "bass", "drums"}
    assert "bass" not in result.skipped_player_ids
    assert "drums" not in result.skipped_player_ids
    assert result.state.intent_for("piano") is not None
    assert result.state.intent_for("bass") is not None
    assert result.state.intent_for("drums") is not None


def test_deciders_do_not_freeze_future_sequence():
    for decider in (PianoNativeDecider(), BassNativeDecider(), DrumsNativeDecider()):
        assert not hasattr(decider, "future_notes")
        assert not hasattr(decider, "future_bar")
        assert not hasattr(decider, "future_score")


def test_factory_builds_executable_trio_runtime():
    loop = build_native_trio_runtime()
    assert set(loop.provider_ids) == {"piano", "bass", "drums"}
