from dataclasses import replace
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import (
    CompingActionType,
    InteractionRole,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoEnsembleMode,
    PianoEnsembleRoleContext,
    PianoHandFunction,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    build_contextual_comping_candidates,
    derive_piano_hand_role_plan,
)
from players.piano.rhythm import rhythmic_intents_for_candidate
from players.piano.variation import (
    GestureSignature,
    VariationContext,
    evaluate_variation,
)


def material():
    return ResolvedHarmonicMaterial(
        affordance_id="test.c7",
        root_pitch_class=0,
        role_pitch_classes={
            "root":(0,),
            "3rd":(4,),
            "b7":(10,),
            "9":(2,),
        },
    )


def test_piano_trio_head_owns_melody_and_lh_comping():
    plan=derive_piano_hand_role_plan(
        PianoEnsembleRoleContext(
            section_role="head",
            piano_is_only_melodic_instrument=True,
        )
    )
    assert plan.mode is PianoEnsembleMode.PIANO_HEAD_TRIO
    assert plan.right_hand is PianoHandFunction.MELODY
    assert plan.left_hand is PianoHandFunction.COMPING
    assert plan.piano_owns_foreground


def test_piano_trio_solo_owns_rh_solo_and_lh_comping():
    plan=derive_piano_hand_role_plan(
        PianoEnsembleRoleContext(
            section_role="piano_solo",
            piano_is_only_melodic_instrument=True,
        )
    )
    assert plan.mode is PianoEnsembleMode.PIANO_SOLO_TRIO
    assert plan.right_hand is PianoHandFunction.IMPROVISED_SOLO
    assert plan.left_hand is PianoHandFunction.COMPING


def test_external_melody_support_allows_two_hand_comping():
    plan=derive_piano_hand_role_plan(
        PianoEnsembleRoleContext(
            section_role="solo",
            external_melody_active=True,
            piano_is_only_melodic_instrument=False,
        )
    )
    assert plan.mode is PianoEnsembleMode.EXTERNAL_MELODY_SUPPORT
    assert plan.right_hand is PianoHandFunction.TWO_HAND_COMPING
    assert plan.allow_two_hand_texture


def test_general_support_has_real_rhythmic_variety():
    ctx=PianoCompingContext()
    request=PianoVoicingRequest(material(),duration_beats=.5)
    slate=build_contextual_comping_candidates(request,ctx)
    support=next(
        c for c in slate.candidates
        if c.action_type is CompingActionType.SPARSE_SUPPORT
        and c.role is InteractionRole.SUPPORT
        and c.realization is not None
    )
    intents=rhythmic_intents_for_candidate(
        support,
        phrase_boundary_probability=.2,
        available_space_beats=0,
        drummer_activity=.7,
    )
    placements={x.placement.value for x in intents}
    cells={x.cell_id for x in intents}
    assert {"on_beat","anticipated","offbeat","delayed"} <= placements
    assert len(cells) >= 6


def test_trio_candidate_factory_exposes_lh_only_comping():
    ctx=PianoCompingContext(ensemble_mode=PianoEnsembleMode.PIANO_SOLO_TRIO)
    request=PianoVoicingRequest(material(),duration_beats=.5)
    slate=build_contextual_comping_candidates(request,ctx)
    lh=[
        c for c in slate.sounding
        if "lh_comping" in c.tags
        and c.realization is not None
        and c.realization.hand_assignment
        and all(hand=="LH" for _,hand in c.realization.hand_assignment)
    ]
    assert lh


def test_trio_evaluator_prefers_lh_only_over_same_rh_occupied_candidate():
    ctx=PianoCompingContext(ensemble_mode=PianoEnsembleMode.PIANO_SOLO_TRIO)
    request=PianoVoicingRequest(material(),duration_beats=.5)
    slate=build_contextual_comping_candidates(request,ctx)
    lh=next(
        c for c in slate.sounding
        if "lh_comping" in c.tags
        and all(hand=="LH" for _,hand in c.realization.hand_assignment)
    )
    first_voice=lh.realization.hand_assignment[0][0]
    rh_assignment=tuple(
        (voice_id, "RH" if voice_id==first_voice else hand)
        for voice_id,hand in lh.realization.hand_assignment
    )
    original=replace(
        lh,
        realization=replace(
            lh.realization,
            hand_assignment=rh_assignment,
        ),
        tags=frozenset(set(lh.tags)-{"lh_comping"}),
    )
    evaluator=PianoCompingEvaluator()
    state=PianoCompingState()
    musical=MusicalContextVector()
    a=evaluator.evaluate(lh,ctx,musical,state)
    b=evaluator.evaluate(original,ctx,musical,state)
    assert a.total>b.total
    assert a.components.get("left_hand_comping_fit",0)>0
    assert b.components.get("foreground_hand_contract",0)<0


def test_repeated_rhythm_cell_gets_variation_pressure():
    class DummyCandidate:
        role=InteractionRole.SUPPORT
        realization=None
        tags=frozenset({"rhythm:on_beat","rhythm_cell:beat_short"})

    recent=[
        GestureSignature("support","piano_shell","on_beat",None,None,None,"beat_short"),
        GestureSignature("support","piano_rootless","on_beat",None,None,None,"beat_short"),
        GestureSignature("support","piano_shell","on_beat",None,None,None,"beat_short"),
    ]
    score=evaluate_variation(
        DummyCandidate(),
        recent,
        VariationContext(
            variation_pressure=1.0,
            groove_lock_strength=0.0,
            motif_continuity_strength=0.0,
            pattern_consistency_strength=0.0,
        ),
    )
    assert score.components.get("rhythm_repetition_streak",0)<0


def test_lh_comping_listens_to_rh_foreground_activity():
    ctx=PianoCompingContext(
        ensemble_mode=PianoEnsembleMode.PIANO_SOLO_TRIO,
        soloist_activity=0.1,
        piano_foreground_activity=0.95,
    )
    request=PianoVoicingRequest(material(),duration_beats=.5)
    slate=build_contextual_comping_candidates(request,ctx)
    silence=next(c for c in slate.candidates if c.realization is None)
    lh=next(
        c for c in slate.sounding
        if "lh_comping" in c.tags
        and all(hand=="LH" for _,hand in c.realization.hand_assignment)
    )
    evaluator=PianoCompingEvaluator()
    state=PianoCompingState()
    musical=MusicalContextVector()
    silence_score=evaluator.evaluate(silence,ctx,musical,state)
    lh_score=evaluator.evaluate(lh,ctx,musical,state)
    assert silence_score.components.get("solo_space",0)>0
    # RH activity should be treated as the current foreground/soloist activity;
    # LH support remains possible but should not behave as an independent metronome.
    assert lh_score.candidate.realization is not None
