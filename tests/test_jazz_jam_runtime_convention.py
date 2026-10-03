from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    PlayerPresence,
    PlayerRole,
    TransportState,
)
from music_intelligence.reasoning.interaction_scheduler import schedule_ensemble
from music_intelligence.reasoning.performance_convention import (
    PerformanceConvention,
    PerformanceConventionMode,
    default_performance_convention,
)


def _quartet_state():
    return EnsembleState(
        transport=TransportState(beat=0.0,bar=0,section="A"),
        players=(
            PlayerPresence("piano","piano",PlayerRole.COMPER),
            PlayerPresence("bass","upright_bass",PlayerRole.BASS),
            PlayerPresence("drums","drum_kit",PlayerRole.DRUMS),
            PlayerPresence("sax","tenor_sax",PlayerRole.SOLOIST),
        ),
        leader_player_id="sax",
    )


def test_jam_session_default_is_visible_to_all_player_directives():
    convention=default_performance_convention("jazz")
    directives=schedule_ensemble(_quartet_state(),convention=convention)
    assert {d.player_id for d in directives} == {"piano","bass","drums","sax"}
    assert all(
        "performance_convention:jazz_jam_session" in d.tags
        for d in directives
    )


def test_explicit_arranged_convention_does_not_get_jam_default_tag():
    arranged=PerformanceConvention(
        genre_family="jazz",
        mode=PerformanceConventionMode.ARRANGED,
        shared_form=True,
        provenance=("test:explicit_arrangement",),
    )
    directives=schedule_ensemble(_quartet_state(),convention=arranged)
    assert all(
        "performance_convention:jazz_jam_session" not in d.tags
        for d in directives
    )
