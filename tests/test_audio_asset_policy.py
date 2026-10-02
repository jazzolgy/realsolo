from pathlib import Path


def test_audio_asset_policy_exists_and_rejects_nc():
    text = Path("docs/AUDIO_ASSET_POLICY.md").read_text(encoding="utf-8")
    assert "NonCommercial" in text
    assert "APPROVED" in text
    assert "CONDITIONAL" in text
    assert "REJECT" in text


def test_manifest_keeps_cc0_defaults_and_ccby_conditional():
    text = Path("config/audio_assets.yaml").read_text(encoding="utf-8")
    assert "karoryfer_meatbass" in text
    assert "virtuosity_drums" in text
    assert "status: approved" in text
    assert "salamander_grand_v3" in text
    assert "mtg_solo_sax" in text
    assert text.count("status: conditional") >= 2
