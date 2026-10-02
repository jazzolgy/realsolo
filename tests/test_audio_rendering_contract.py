from pathlib import Path


def test_soundfont_adapter_is_pinned_and_keeps_fallback():
    path = Path("realtime/ensemble_app/web/soundfont_engine.js")
    text = path.read_text(encoding="utf-8")
    assert "spessasynth_lib@4.3.14" in text
    assert "WorkletSynthesizer" in text
    assert "noteOn" in text
    assert "noteOff" in text


def test_stage1_ui_exposes_soundfont_loader():
    text = Path("realtime/ensemble_app/web/index.html").read_text(encoding="utf-8")
    assert 'id="soundfont"' in text
    assert "sampleReady()" in text
    assert "oscillator" in text
