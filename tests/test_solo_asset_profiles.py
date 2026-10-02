from realtime.ensemble_app.asset_installer import (
    _trumpet_filename,
    _trumpet_profile_spec,
)
from realtime.ensemble_app.solo_articulation import (
    SoloArticulation,
    SoloRenderIntent,
    choose_sample_family,
)


def test_trumpet_profiles_scale_from_full_to_mini():
    full = _trumpet_profile_spec("full")
    lite = _trumpet_profile_spec("lite")
    mini = _trumpet_profile_spec("mini")
    assert "vibrato" in full
    assert "vibrato" in lite
    assert "vibrato" not in mini
    assert len(full["short"][0]) > len(mini["short"][0])


def test_trumpet_filename_maps_accidentals():
    assert _trumpet_filename("sus", "Ds3", 3) == "Sum_SHTrumpet_sus_D#3_v3_rr1.wav"


def test_growl_and_subtone_families_remain_explicit():
    growl = SoloRenderIntent(
        "baritone_sax", 50, 80, .75,
        articulation=(SoloArticulation.GROWL,),
    )
    subtone = SoloRenderIntent(
        "tenor_sax", 55, 72, 1.0,
        articulation=(SoloArticulation.SUBTONE,),
    )
    assert choose_sample_family(growl) == "growl"
    assert choose_sample_family(subtone) == "subtone"
