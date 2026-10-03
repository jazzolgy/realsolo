from ._boundary_utils import forbidden_imports


def test_audio_evidence_does_not_depend_on_downstream_or_player_internals():
    findings = forbidden_imports(
        "src/music_intelligence/audio_evidence",
        (
            "music_intelligence.transcribe.notation",
            "music_intelligence.transcribe.score",
            "music_intelligence.transcribe.engraving",
            "music_intelligence.transcribe.layout",
            "music_intelligence.transcribe.musicxml",
            "music_intelligence.learning",
            "players",
        ),
    )
    assert findings == [], f"Audio Evidence boundary violations: {findings}"


def test_audio_evidence_may_only_cross_transcribe_boundary_through_events_contract():
    findings = forbidden_imports(
        "src/music_intelligence/audio_evidence",
        ("music_intelligence.transcribe",),
    )
    illegal = [
        item for item in findings
        if item[1] != "music_intelligence.transcribe.events"
    ]
    assert illegal == [], f"Audio Evidence imported Transcription internals: {illegal}"
