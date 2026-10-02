from pathlib import Path
from tempfile import TemporaryDirectory

from realtime.ensemble_app.asset_installer import _parse_simple_sfz


def test_simple_sfz_parser_keeps_velocity_key_and_rr():
    with TemporaryDirectory() as td:
        root = Path(td)
        sample = root / "a.wav"
        sample.write_bytes(b"RIFF")
        sfz = root / "x.sfz"
        sfz.write_text(
            "<group> lokey=36 hikey=38 lovel=65 hivel=96 pitch_keycenter=37\n"
            "<region> sample=a.wav seq_position=2\n",
            encoding="utf-8",
        )
        rows = _parse_simple_sfz(sfz)
        assert rows[0]["lokey"] == 36
        assert rows[0]["hivel"] == 96
        assert rows[0]["pitch_keycenter"] == 37
        assert rows[0]["rr"] == 2


def test_approved_sample_engine_is_present():
    text = Path("realtime/ensemble_app/web/approved_sample_engine.js").read_text(encoding="utf-8")
    assert "Karoryfer" not in text  # renderer consumes manifest, not library-specific policy
    assert "decodeAudioData" in text
    assert "playbackRate" in text
