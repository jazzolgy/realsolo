from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from music_intelligence.reasoning.legend_style_core import CandidateEvent
from players.piano import (
    BebopHarmonicPhase,
    BebopTurnTakingEvidence,
    BebopTurnTakingType,
    CompingActionType,
    InteractionRole,
    PianoCompingCandidate,
    PianoSoloContext,
    PianoSoloEvaluator,
    derive_bebop_harmonic_turn_context,
    evaluate_bebop_harmonic_turn_comping_bias,
)


def turn(kind=BebopTurnTakingType.SUPPORTED_HANDOFF_REENTRY):
    return BebopTurnTakingEvidence(
        kind,
        0.2,
        0.9,
        0.7,
        4.0,
        1.0,
        0.0,
    )


def frame(function, *, phrase=0.3, tension=0.3, next_symbol=None):
    nxt=None
    if next_symbol is not None:
        nxt=HarmonicEvidence(
            HarmonySource.EXPECTED,
            symbol=next_symbol,
            function="tonic",
        )
    return HarmonicFrame(
        expected=HarmonicEvidence(
            HarmonySource.EXPECTED,
            symbol="G7" if "dominant" in function else "Cmaj7",
            function=function,
        ),
        next_expected=nxt,
        phrase_position=phrase,
        tension=tension,
        cadence_state="open",
    )


def test_stable_field_context():
    ctx=derive_bebop_harmonic_turn_context(
        frame("tonic",tension=0.2),
        turn(),
    )
    assert ctx.phase is BebopHarmonicPhase.STABLE_FIELD
    assert ctx.stability_strength >= 0.5


def test_directed_resolution_context():
    ctx=derive_bebop_harmonic_turn_context(
        frame("dominant",tension=0.75),
        turn(),
    )
    assert ctx.phase is BebopHarmonicPhase.DIRECTED_RESOLUTION
    assert ctx.resolution_strength >= 0.65


def test_anticipatory_context_when_next_harmony_known():
    ctx=derive_bebop_harmonic_turn_context(
        frame("tonic",next_symbol="Dm7"),
        turn(),
    )
    assert ctx.phase is BebopHarmonicPhase.ANTICIPATORY
    assert ctx.anticipation_strength >= 0.65


def test_form_boundary_overrides_other_phases():
    f=frame("dominant",phrase=0.98,tension=0.8,next_symbol="Cmaj7")
    f=HarmonicFrame(
        expected=f.expected,
        next_expected=f.next_expected,
        phrase_position=0.98,
        tension=0.8,
        cadence_state="cadential",
    )
    ctx=derive_bebop_harmonic_turn_context(f,turn())
    assert ctx.phase is BebopHarmonicPhase.FORM_BOUNDARY
    assert ctx.phrase_boundary_pressure >= 0.65


def test_solo_anticipation_biases_pickup():
    harmonic_turn=derive_bebop_harmonic_turn_context(
        frame("tonic",next_symbol="Dm7"),
        turn(),
    )
    evaluator=PianoSoloEvaluator()
    ctx=PianoSoloContext(harmonic_turn=harmonic_turn)
    anticipated=CandidateEvent(
        69,
        0.5,
        onset_offset_beats=-0.125,
        tags=frozenset({"anticipation","pickup","next_harmony_target"}),
    )
    plain=CandidateEvent(
        69,
        0.5,
        tags=frozenset({"chord_tone"}),
    )
    a=evaluator.evaluate(anticipated,ctx)
    b=evaluator.evaluate(plain,ctx)
    assert a.components.get("harmonic_turn_anticipation",0)>0
    assert a.total>b.total


def test_solo_directed_resolution_rewards_target_path():
    harmonic_turn=derive_bebop_harmonic_turn_context(
        frame("dominant",tension=0.8),
        turn(),
    )
    evaluator=PianoSoloEvaluator()
    ctx=PianoSoloContext(harmonic_turn=harmonic_turn)
    directed=CandidateEvent(
        71,
        0.5,
        tags=frozenset({"directed_target","resolution_path","guide_tone"}),
    )
    score=evaluator.evaluate(directed,ctx)
    assert score.components.get("harmonic_turn_resolution",0)>0


def test_boundary_collective_release_reinforces_comping_space():
    harmonic_turn=derive_bebop_harmonic_turn_context(
        HarmonicFrame(
            expected=HarmonicEvidence(
                HarmonySource.EXPECTED,
                symbol="G7",
                function="dominant",
            ),
            phrase_position=0.99,
            tension=0.8,
            cadence_state="cadential",
        ),
        turn(BebopTurnTakingType.COLLECTIVE_RELEASE_REENTRY),
    )
    silence=PianoCompingCandidate(
        action_type=CompingActionType.SILENCE,
        role=InteractionRole.LAY_OUT,
        duration_beats=0.5,
    )
    score=evaluate_bebop_harmonic_turn_comping_bias(
        silence,
        harmonic_turn,
    )
    assert score.components.get("boundary_space",0)>0
    assert score.components.get("release_boundary_alignment",0)>0


def test_harmonic_turn_context_contains_no_future_note_plan():
    ctx=derive_bebop_harmonic_turn_context(
        frame("dominant",next_symbol="Cmaj7"),
        turn(),
    )
    assert not hasattr(ctx,"future_notes")
    assert not hasattr(ctx,"future_phrase")
    assert not hasattr(ctx,"planned_sequence")
