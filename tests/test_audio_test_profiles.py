from realtime.ensemble_app.asset_installer import (
    PROFILES,
    _sampled_manifest,
    _LITE_BASS_ANCHORS,
    _LITE_BASS_LAYERS,
    _LITE_BASS_RR,
    _MINI_BASS_ANCHORS,
    _MINI_BASS_LAYERS,
    _MINI_BASS_RR,
    _DRUM_LITE,
    _DRUM_MINI,
)


def test_three_profiles_are_declared():
    assert PROFILES == ("full", "lite", "mini")


def test_lite_is_denser_than_mini():
    lite = _sampled_manifest(
        "lite", _LITE_BASS_ANCHORS, _LITE_BASS_LAYERS, _LITE_BASS_RR, _DRUM_LITE
    )
    mini = _sampled_manifest(
        "mini", _MINI_BASS_ANCHORS, _MINI_BASS_LAYERS, _MINI_BASS_RR, _DRUM_MINI
    )
    assert len(lite["packs"]["bass"]["regions"]) == 32
    assert len(mini["packs"]["bass"]["regions"]) == 4
    assert sum(map(len, lite["packs"]["drums"]["articulations"].values())) > sum(
        map(len, mini["packs"]["drums"]["articulations"].values())
    )


def test_profiles_keep_identical_role_mapping():
    lite = _sampled_manifest(
        "lite", _LITE_BASS_ANCHORS, _LITE_BASS_LAYERS, _LITE_BASS_RR, _DRUM_LITE
    )
    mini = _sampled_manifest(
        "mini", _MINI_BASS_ANCHORS, _MINI_BASS_LAYERS, _MINI_BASS_RR, _DRUM_MINI
    )
    assert lite["packs"]["drums"]["gm_map"] == mini["packs"]["drums"]["gm_map"]
