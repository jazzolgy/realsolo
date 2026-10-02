from pathlib import Path

from players.bass.immediate_realizer import BassContext as CanonicalBassContext
from music_intelligence.bass.immediate_realizer import BassContext as LegacyBassContext
from players.drums.online_drummer import DrummerPerformanceMemory as CanonicalDrumMemory
from music_intelligence.drums.online_drummer import DrummerPerformanceMemory as LegacyDrumMemory


def test_bass_implementation_is_canonical_under_players():
    root = Path(__file__).resolve().parents[1]
    canonical = (root / "players/bass/immediate_realizer.py").read_text(encoding="utf-8")
    legacy = (root / "src/music_intelligence/bass/immediate_realizer.py").read_text(encoding="utf-8")
    assert "class BassContext" in canonical
    assert "Canonical module: players.bass.immediate_realizer" in legacy
    assert LegacyBassContext is CanonicalBassContext


def test_drums_implementation_is_canonical_under_players():
    root = Path(__file__).resolve().parents[1]
    canonical = (root / "players/drums/online_drummer.py").read_text(encoding="utf-8")
    legacy = (root / "src/music_intelligence/drums/online_drummer.py").read_text(encoding="utf-8")
    assert "class DrummerPerformanceMemory" in canonical
    assert "Canonical module: players.drums.online_drummer" in legacy
    assert LegacyDrumMemory is CanonicalDrumMemory
