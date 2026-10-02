from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import (
    BebopHarmonicPhase,
    BebopHarmonicTurnContext,
    BebopTurnTakingEvidence,
    BebopTurnTakingType,
    EnsembleBreathType,
    EnsembleComplementarityEvidence,
    PianoSoloContext,
    PianoSoloEvaluator,
    PianoSoloState,
    ResolvedHarmonicMaterial,
    build_bebop_solo_tick,
    perform_bebop_solo_tick,
)


def current_material():
    return ResolvedHarmonicMaterial(
        affordance_id="g7",
        root_pitch_class=7,
        role_pitch_classes={
            "root": (7,),
            "3rd": (11,),
            "b7": (5,),
        },
    )


def next_material():
    return ResolvedHarmonicMaterial(
        affordance_id="cmaj7",
        root_pitch_class=0,
        role_pitch_classes={
            "root": (0,),
            "3rd": (4,),
            "7th": (11,),
        },
    )


def test_end_to_end_anticipatory_tick_builds_next_harmony_candidates():
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
    tick=build_bebop_solo_tick(
        current_material=current_material(),
        next_material=next_material(),
        harmonic_turn=harmonic,
        turn=turn,
        complementarity=comp,
        previous_pitch_midi=67,
        low_midi=60,
        high_midi=84,
    )
    assert tick.intent.target_mode.value=="next_harmony"
    assert any("next_harmony_target" in c.tags for c in tick.candidates if c.pitch_midi is not None)


def test_end_to_end_tick_commits_exactly_one_event():
    turn=BebopTurnTakingEvidence(
        BebopTurnTakingType.AMBIGUOUS,
        0.4,0.7,0.7,2.0,0.8,0.0,
    )
    comp=EnsembleComplementarityEvidence(
        breath_type=EnsembleBreathType.NONE,
        confidence=0.5,
    )
    harmonic=BebopHarmonicTurnContext(
        phase=BebopHarmonicPhase.DIRECTED_RESOLUTION,
        turn_type=turn.episode_type,
        resolution_strength=0.9,
        confidence=0.9,
    )
    tick=build_bebop_solo_tick(
        current_material=current_material(),
        harmonic_turn=harmonic,
        turn=turn,
        complementarity=comp,
        previous_pitch_midi=67,
    )

    evaluator=PianoSoloEvaluator()
    state=PianoSoloState()
    context=PianoSoloContext(
        musical=MusicalContextVector(
            phrase_maturity=0.5,
            recent_chord_identity_strength=0.7,
        ),
        harmonic_turn=harmonic,
        turn_taking=turn,
        ensemble_complementarity=comp,
    )
    chosen=perform_bebop_solo_tick(
        tick=tick,
        evaluator=evaluator,
        context=context,
        state=state,
    )
    assert len(state.memory.committed)==1
    assert state.memory.committed[0]==chosen.candidate


def test_tick_plan_contains_no_future_phrase_sequence():
    turn=BebopTurnTakingEvidence(
        BebopTurnTakingType.AMBIGUOUS,
        0.4,0.7,0.7,2.0,0.8,0.0,
    )
    comp=EnsembleComplementarityEvidence(
        breath_type=EnsembleBreathType.NONE,
        confidence=0.5,
    )
    harmonic=BebopHarmonicTurnContext(
        phase=BebopHarmonicPhase.STABLE_FIELD,
        turn_type=turn.episode_type,
        stability_strength=0.8,
        confidence=0.8,
    )
    tick=build_bebop_solo_tick(
        current_material=current_material(),
        harmonic_turn=harmonic,
        turn=turn,
        complementarity=comp,
        previous_pitch_midi=67,
    )
    assert not hasattr(tick,"future_notes")
    assert not hasattr(tick,"phrase_sequence")
    assert all(not hasattr(c,"future_notes") for c in tick.candidates)
