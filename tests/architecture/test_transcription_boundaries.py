from ._boundary_utils import forbidden_imports


def test_transcription_does_not_import_audio_engine_internals():
    findings = forbidden_imports(
        "src/music_intelligence/transcribe",
        (
            "music_intelligence.audio_evidence.observation",
            "music_intelligence.audio_evidence.posterior",
            "music_intelligence.audio_evidence.detectors",
            "music_intelligence.audio_evidence.calibration",
        ),
    )
    assert findings == [], f"Transcription depends on Audio Evidence internals: {findings}"


def test_transcription_does_not_depend_on_players_or_realtime():
    findings = forbidden_imports(
        "src/music_intelligence/transcribe",
        ("players", "realtime"),
    )
    assert findings == [], f"Transcription product boundary violations: {findings}"
