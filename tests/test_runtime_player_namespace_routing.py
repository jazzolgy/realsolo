from pathlib import Path

import realtime.ensemble_app.native_deciders as native_deciders
import realtime.ensemble_app.native_trio_players as native_trio_players
from players import bass as bass_player
from players import drums as drums_player


def test_runtime_native_deciders_use_player_namespace_objects():
    assert native_deciders.BassContext is bass_player.BassContext
    assert native_deciders.BassPerformanceMemory is bass_player.BassPerformanceMemory
    assert native_deciders.DrummerRuntimeContext is drums_player.DrummerRuntimeContext
    assert native_deciders.DrummerPerformanceMemory is drums_player.DrummerPerformanceMemory


def test_stage1_native_players_use_player_namespace_objects():
    assert native_trio_players.BassContext is bass_player.BassContext
    assert native_trio_players.DrummerRuntimeContext is drums_player.DrummerRuntimeContext


def test_runtime_sources_do_not_import_bass_or_drums_directly_from_music_intelligence():
    root = Path(__file__).resolve().parents[1]
    for rel in (
        "realtime/ensemble_app/native_deciders.py",
        "realtime/ensemble_app/native_trio_players.py",
    ):
        source = (root / rel).read_text(encoding="utf-8")
        assert "from music_intelligence.bass import" not in source
        assert "from music_intelligence.drums import" not in source
        assert "from players.bass import" in source
        assert "from players.drums import" in source
