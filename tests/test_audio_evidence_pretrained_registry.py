from music_intelligence.audio_evidence.detectors.pretrained_registry import (
    pretrained_profile,
    pretrained_profiles_for_task,
)


def test_pretrained_registry_distinguishes_separator_and_tagger_roles():
    separators = pretrained_profiles_for_task("source_separation")
    assert {item.model_id for item in separators} == {
        "demucs:htdemucs_6s",
        "torchaudio:HDEMUCS_HIGH_MUSDB_PLUS",
    }

    yamnet = pretrained_profile("yamnet:audioset")
    assert yamnet.note_level is False
    assert yamnet.default_role == "weak_instrument_prior"


def test_six_stem_demucs_profile_explicitly_contains_bass_and_piano():
    profile = pretrained_profile("demucs:htdemucs_6s")

    assert "bass" in profile.classes_or_stems
    assert "piano" in profile.classes_or_stems
    assert profile.deployment_review_required is True
