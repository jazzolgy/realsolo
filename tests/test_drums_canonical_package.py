from pathlib import Path

from players.drums.online_drummer import DrummerPerformanceMemory as CanonicalDrumMemory
from music_intelligence.drums.online_drummer import DrummerPerformanceMemory as LegacyDrumMemory
from players.drums.ride_continuity import __name__ as ride_module_name
from players.drums.standard100_practice import __name__ as practice_module_name


def test_drums_implementation_lives_under_players():
    root = Path(__file__).resolve().parents[1]
    canonical = (root / "players/drums/online_drummer.py").read_text(encoding="utf-8")
    legacy = (root / "src/music_intelligence/drums/online_drummer.py").read_text(encoding="utf-8")
    assert "class DrummerPerformanceMemory" in canonical
    assert "Legacy compatibility alias" in legacy
    assert LegacyDrumMemory is CanonicalDrumMemory


def test_branch_specific_drum_modules_moved_too():
    assert ride_module_name == "players.drums.ride_continuity"
    assert practice_module_name == "players.drums.standard100_practice"
