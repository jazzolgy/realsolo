from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from music_intelligence.harmony.scale_linear_core import (
    LinearRouteKind,
    build_linear_connection_affordances,
)
from players.piano import (
    BebopHarmonicPhase,
    BebopHarmonicTurnContext,
    BebopTurnTakingEvidence,
    BebopTurnTakingType,
    EnsembleBreathType,
    EnsembleComplementarityEvidence,
    ResolvedHarmonicMaterial,
    build_bebop_solo_tick,
    realize_shared_linear_affordances,
)


def ev(root, symbol, pcs, function=None):
    return HarmonicEvidence(
        HarmonySource.EXPECTED,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
        function=function,
    )


def test_piano_adapter_realizes_shared_routes_without_future_sequence():
    frame=HarmonicFrame(
        expected=ev(0,"Cm7",{0,3,7,10},"tonic"),
        next_expected=ev(5,"F7",{5,9,0,3},"dominant"),
    )
    routes=build_linear_connection_affordances(
        frame,
        current_pitch_class=3,
        target_pitch_classes=frozenset({5,9}),
        local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
    )
    events=realize_shared_linear_affordances(
        routes,
        anchor_midi=67,
        low_midi=60,
        high_midi=84,
    )
    assert events
    assert any("shared_linear" in e.tags for e in events)
    assert any(
        f"linear_route:{LinearRouteKind.APPROACH.value}" in e.tags
        for e in events
    )
    assert all(60 <= e.pitch_midi <= 84 for e in events if e.pitch_midi is not None)
    assert all(not hasattr(e,"future_notes") for e in events)


def test_runtime_consumes_shared_linear_routes_when_harmonic_frame_present():
    turn=BebopTurnTakingEvidence(
        BebopTurnTakingType.AMBIGUOUS,
        0.4,0.7,0.7,2.0,0.8,0.0,
    )
    comp=EnsembleComplementarityEvidence(
        breath_type=EnsembleBreathType.NONE,
        confidence=0.5,
    )
    harmonic=BebopHarmonicTurnContext(
        phase=BebopHarmonicPhase.ANTICIPATORY,
        turn_type=turn.episode_type,
        anticipation_strength=0.9,
        confidence=0.9,
    )
    current=ResolvedHarmonicMaterial(
        affordance_id="cm7",
        root_pitch_class=0,
        role_pitch_classes={
            "root":(0,),
            "b3":(3,),
            "b7":(10,),
        },
    )
    nxt=ResolvedHarmonicMaterial(
        affordance_id="f7",
        root_pitch_class=5,
        role_pitch_classes={
            "root":(5,),
            "3rd":(9,),
            "b7":(3,),
        },
    )
    frame=HarmonicFrame(
        expected=ev(0,"Cm7",{0,3,7,10},"tonic"),
        next_expected=ev(5,"F7",{5,9,0,3},"dominant"),
    )
    tick=build_bebop_solo_tick(
        current_material=current,
        next_material=nxt,
        harmonic_turn=harmonic,
        turn=turn,
        complementarity=comp,
        previous_pitch_midi=63,
        harmonic_frame=frame,
        local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
        low_midi=60,
        high_midi=84,
    )
    assert any("shared_linear" in c.tags for c in tick.candidates)
    assert any("next_harmony_target" in c.tags for c in tick.candidates)
    assert any("close_approach" in c.tags for c in tick.candidates)


def test_no_local_connector_duplication_when_shared_routes_supplied():
    frame=HarmonicFrame(
        expected=ev(0,"Cm7",{0,3,7,10}),
        next_expected=ev(5,"F7",{5,9,0,3}),
    )
    routes=build_linear_connection_affordances(
        frame,
        current_pitch_class=3,
        target_pitch_classes=frozenset({5,9}),
    )
    events=realize_shared_linear_affordances(
        routes,
        anchor_midi=63,
        low_midi=60,
        high_midi=84,
    )
    approach_events=[e for e in events if "close_approach" in e.tags]
    assert approach_events
    assert all("shared_linear" in e.tags for e in approach_events)
