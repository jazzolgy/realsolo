from music_intelligence import bass as bass_impl
from music_intelligence import drums as drums_impl
from players import bass as bass_player
from players import drums as drums_player


def test_bass_player_namespace_is_compatibility_facade():
    assert set(bass_player.__all__) == set(bass_impl.__all__)
    for name in bass_player.__all__:
        assert getattr(bass_player, name) is getattr(bass_impl, name)


def test_drums_player_namespace_is_compatibility_facade():
    assert set(drums_player.__all__) == set(drums_impl.__all__)
    for name in drums_player.__all__:
        assert getattr(drums_player, name) is getattr(drums_impl, name)
