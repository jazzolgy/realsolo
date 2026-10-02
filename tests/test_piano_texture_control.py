from players.piano import (
    AttackDensityLevel,
    HarmonicColorLevel,
    MacroArcPhase,
    PianoCompingContext,
    PianoEnsembleMode,
    PianoTextureIntent,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    build_contextual_comping_candidates,
    classify_lh_texture,
    evaluate_texture_intent,
)
from players.piano.lh_texture import LHTextureClass


def material():
    return ResolvedHarmonicMaterial(
        affordance_id="test.fmaj",
        root_pitch_class=5,
        role_pitch_classes={
            "root":(5,),
            "3rd":(9,),
            "7th":(4,),
            "9":(7,),
            "13":(2,),
        },
    )


def slate():
    return build_contextual_comping_candidates(
        PianoVoicingRequest(material(),duration_beats=.5),
        PianoCompingContext(
            ensemble_mode=PianoEnsembleMode.PIANO_SOLO_TRIO,
            piano_foreground_activity=.4,
            bass_activity=.7,
        ),
    )


def test_rich_color_can_prefer_two_tension_without_high_attack_density():
    s=slate()
    rich=next(c for c in s.candidates if classify_lh_texture(c) is LHTextureClass.TWO_TENSION)
    silence=next(c for c in s.candidates if c.realization is None)

    intent=PianoTextureIntent(
        harmonic_color=HarmonicColorLevel.RICH,
        attack_density=AttackDensityLevel.LOW,
        macro_arc=MacroArcPhase.OPEN,
        confidence=1.0,
    )

    rich_bias=evaluate_texture_intent(rich,intent)
    silence_bias=evaluate_texture_intent(silence,intent)

    assert rich_bias.components.get("texture_color_fit",0)>0
    assert silence_bias.components.get("texture_attack_fit",0)>0
    assert silence_bias.components.get("macro_arc_fit",0)>0


def test_thin_color_and_high_attack_are_independent_axes():
    s=slate()
    guide=next(c for c in s.candidates if classify_lh_texture(c) is LHTextureClass.GUIDE_DYAD)
    intent=PianoTextureIntent(
        harmonic_color=HarmonicColorLevel.THIN,
        attack_density=AttackDensityLevel.HIGH,
        macro_arc=MacroArcPhase.INTENSIFY,
        confidence=1.0,
    )
    result=evaluate_texture_intent(guide,intent)
    assert result.components.get("texture_color_fit",0)>0


def test_release_arc_favors_space_and_rejects_build():
    s=slate()
    silence=next(c for c in s.candidates if c.realization is None)
    build=next(c for c in s.candidates if getattr(c.role,"value","")=="build")
    intent=PianoTextureIntent(
        macro_arc=MacroArcPhase.RELEASE,
        confidence=1.0,
    )
    a=evaluate_texture_intent(silence,intent)
    b=evaluate_texture_intent(build,intent)
    assert a.components.get("macro_arc_fit",0)>0
    assert b.components.get("macro_arc_conflict",0)<0


def test_texture_intent_never_contains_future_notes():
    intent=PianoTextureIntent()
    assert not hasattr(intent,"future_notes")
    assert not hasattr(intent,"future_pattern")
