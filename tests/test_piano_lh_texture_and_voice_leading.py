from dataclasses import replace

from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import (
    LHTextureClass,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoEnsembleMode,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    build_contextual_comping_candidates,
    classify_lh_texture,
    evaluate_lh_texture_bias,
)


def material():
    return ResolvedHarmonicMaterial(
        affordance_id="test.g7",
        root_pitch_class=7,
        role_pitch_classes={
            "root": (7,),
            "3rd": (11,),
            "b7": (5,),
            "9": (9,),
            "13": (4,),
            "b9": (8,),
        },
    )


def trio_context(**kwargs):
    base=dict(
        ensemble_mode=PianoEnsembleMode.PIANO_SOLO_TRIO,
        piano_foreground_activity=.45,
        bass_activity=.7,
        ensemble_density=.45,
        tension_preference=.75,
    )
    base.update(kwargs)
    return PianoCompingContext(**base)


def test_candidate_factory_contains_guide_one_two_tension_and_root_anchor():
    slate=build_contextual_comping_candidates(
        PianoVoicingRequest(material(),duration_beats=.5),
        trio_context(),
    )
    textures={classify_lh_texture(c) for c in slate.candidates}
    assert LHTextureClass.LAY_OUT in textures
    assert LHTextureClass.GUIDE_DYAD in textures
    assert LHTextureClass.ONE_TENSION in textures
    assert LHTextureClass.TWO_TENSION in textures
    assert LHTextureClass.ROOT_ANCHOR in textures


def test_two_tension_is_normal_color_in_open_trio_space():
    slate=build_contextual_comping_candidates(
        PianoVoicingRequest(material(),duration_beats=.5),
        trio_context(available_space_beats=1.0,piano_foreground_activity=.3),
    )
    candidate=next(
        c for c in slate.candidates
        if classify_lh_texture(c) is LHTextureClass.TWO_TENSION
    )
    bias=evaluate_lh_texture_bias(candidate,trio_context(available_space_beats=1.0,piano_foreground_activity=.3))
    assert bias.components.get("lh_two_tension_default",0)>0
    assert bias.components.get("lh_two_tension_space",0)>0


def test_guide_dyad_is_rewarded_when_rh_is_busy():
    slate=build_contextual_comping_candidates(
        PianoVoicingRequest(material(),duration_beats=.5),
        trio_context(piano_foreground_activity=.95),
    )
    candidate=next(
        c for c in slate.candidates
        if classify_lh_texture(c) is LHTextureClass.GUIDE_DYAD
    )
    bias=evaluate_lh_texture_bias(candidate,trio_context(piano_foreground_activity=.95))
    assert bias.components.get("lh_guide_busy_fit",0)>0


def test_root_anchor_is_discouraged_when_bass_is_active():
    slate=build_contextual_comping_candidates(
        PianoVoicingRequest(material(),duration_beats=.5),
        trio_context(bass_activity=.9),
    )
    root=next(
        c for c in slate.candidates
        if classify_lh_texture(c) is LHTextureClass.ROOT_ANCHOR
    )
    bias=evaluate_lh_texture_bias(root,trio_context(bass_activity=.9))
    assert bias.components.get("lh_root_duplication",0)<0


def test_root_anchor_can_become_structural_when_bass_leaves_space():
    slate=build_contextual_comping_candidates(
        PianoVoicingRequest(material(),duration_beats=.5),
        trio_context(bass_activity=.15,phrase_boundary_probability=.9),
    )
    root=next(
        c for c in slate.candidates
        if classify_lh_texture(c) is LHTextureClass.ROOT_ANCHOR
    )
    bias=evaluate_lh_texture_bias(
        root,
        trio_context(bass_activity=.15,phrase_boundary_probability=.9),
    )
    assert bias.components.get("lh_root_bass_space",0)>0
    assert bias.components.get("lh_root_structural_cue",0)>0


def test_comping_evaluator_rewards_connected_lh_voice_leading():
    ctx=trio_context()
    slate=build_contextual_comping_candidates(
        PianoVoicingRequest(material(),duration_beats=.5),
        ctx,
    )
    lh_candidates=[
        c for c in slate.candidates
        if c.realization is not None
        and c.realization.hand_assignment
        and all(hand=="LH" for _,hand in c.realization.hand_assignment)
        and classify_lh_texture(c) in {LHTextureClass.ONE_TENSION,LHTextureClass.TWO_TENSION}
    ]
    assert lh_candidates
    first=lh_candidates[0]

    state=PianoCompingState()
    state.commit(first)

    # Same connected realization should receive continuity components.
    evaluator=PianoCompingEvaluator()
    score=evaluator.evaluate(
        first,
        ctx,
        MusicalContextVector(),
        state,
    )
    assert score.components.get("lh_common_tone_continuity",0)>0
    assert score.components.get("lh_smooth_voice_motion",0)>0
    assert score.components.get("lh_top_voice_line",0)>0


def test_lh_texture_does_not_force_sound_when_rh_is_busy():
    ctx=trio_context(piano_foreground_activity=.96,ensemble_density=.8)
    slate=build_contextual_comping_candidates(
        PianoVoicingRequest(material(),duration_beats=.5),
        ctx,
    )
    silence=next(c for c in slate.candidates if c.realization is None)
    bias=evaluate_lh_texture_bias(silence,ctx)
    assert bias.components.get("lh_texture_space",0)>0
