from ._boundary_utils import forbidden_imports


def test_shared_reasoning_does_not_import_player_implementations():
    findings = forbidden_imports(
        "src/music_intelligence/reasoning",
        ("players",),
    )
    assert findings == [], f"Shared Core imports Player internals: {findings}"


def test_shared_harmony_does_not_import_player_or_realtime_implementations():
    findings = forbidden_imports(
        "src/music_intelligence/harmony",
        ("players", "realtime"),
    )
    assert findings == [], f"Shared harmony boundary violations: {findings}"
