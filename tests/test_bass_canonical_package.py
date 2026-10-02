from pathlib import Path

from players.bass.immediate_realizer import BassContext as CanonicalBassContext
from music_intelligence.bass.immediate_realizer import BassContext as LegacyBassContext
from players.bass.practice_curriculum import __name__ as practice_module_name


def test_bass_implementation_lives_under_players():
    root = Path(__file__).resolve().parents[1]
    canonical = (root / "players/bass/immediate_realizer.py").read_text(encoding="utf-8")
    legacy = (root / "src/music_intelligence/bass/immediate_realizer.py").read_text(encoding="utf-8")
    assert "class BassContext" in canonical
    assert "Legacy compatibility alias" in legacy
    assert LegacyBassContext is CanonicalBassContext


def test_branch_specific_bass_modules_moved_too():
    assert practice_module_name == "players.bass.practice_curriculum"
