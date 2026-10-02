from music_intelligence.harmony.scale_linear_core import (
    LinearConnectionAffordance,
    LinearRouteKind,
)
from music_intelligence.reasoning.solo_grammar import SoloDevelopmentOperation
from players.piano import (
    BebopDensityDirection,
    BebopEntryMode,
    BebopPhraseIntent,
    BebopTargetMode,
    ResolvedHarmonicMaterial,
)
from players.piano.bebop_solo_candidates import generate_immediate_bebop_candidates


def material():
    return ResolvedHarmonicMaterial(
        affordance_id="test.dm7",
        root_pitch_class=2,
        role_pitch_classes={
            "root":(2,),
            "b3":(5,),
            "b7":(0,),
            "9":(4,),
        },
    )


def intent(density=BebopDensityDirection.STABLE):
    return BebopPhraseIntent(
        horizon_beats=2.0,
        entry_mode=BebopEntryMode.CONTINUE,
        target_mode=BebopTargetMode.GUIDE_TONE,
        density_direction=density,
        connector_families=("passing","neighbor","close_approach"),
        solo_method=SoloDevelopmentOperation.STATE,
        confidence=.8,
    )


def test_motion_tags_activate_parker_symbolic_prior_features():
    events=generate_immediate_bebop_candidates(
        current_material=material(),
        intent=intent(),
        previous_pitch_midi=60,
        low_midi=55,
        high_midi=76,
    )
    assert any("step_motion" in e.tags for e in events if e.pitch_midi is not None)
    assert any("within_p4_motion" in e.tags for e in events if e.pitch_midi is not None)


def test_contextual_triplet_variants_exist_but_do_not_replace_surface():
    events=generate_immediate_bebop_candidates(
        current_material=material(),
        intent=intent(BebopDensityDirection.STABLE),
        previous_pitch_midi=60,
        low_midi=55,
        high_midi=76,
    )
    assert any("triplet" in e.tags for e in events)
    assert any("triplet" not in e.tags for e in events)


def test_release_rest_gets_parker_phrase_space_tag():
    events=generate_immediate_bebop_candidates(
        current_material=material(),
        intent=intent(BebopDensityDirection.RELEASE),
        previous_pitch_midi=60,
        low_midi=55,
        high_midi=76,
    )
    rests=[e for e in events if e.pitch_midi is None]
    assert rests
    assert any("rest_half_beat" in e.tags or "rest_one_beat" in e.tags for e in rests)
