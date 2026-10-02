from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    InteractionKind,
    PlayerActionIntent,
    PlayerPresence,
    PlayerRole,
    TransportState,
    update_player_intent,
)
from music_intelligence.reasoning.interaction_scheduler import (
    directive_to_intent,
    schedule_ensemble,
    schedule_player,
)


def state(form_position=.4):
    return EnsembleState(
        transport=TransportState(
            beat=1.0, bar=8, section="A", form_position=form_position
        ),
        players=(
            PlayerPresence("piano", "piano", PlayerRole.COMPER),
            PlayerPresence("bass", "bass", PlayerRole.BASS),
            PlayerPresence("drums", "drums", PlayerRole.DRUMS),
            PlayerPresence("sax", "tenor_sax", PlayerRole.SOLOIST),
        ),
    )


def with_sax_lead(*, phrase_maturity=.4, density=.7):
    s = state()
    return update_player_intent(s, PlayerActionIntent(
        "sax",
        InteractionKind.LEAD,
        density=density,
        energy=.75,
        leadership=.92,
        phrase_maturity=phrase_maturity,
    ))


def test_strong_sax_leader_makes_piano_yield():
    d = schedule_player(with_sax_lead(), "piano")
    assert d.interaction is InteractionKind.YIELD
    assert d.density_delta < 0
    assert d.target_player_ids == ("sax",)


def test_bass_locks_under_active_leader_instead_of_disappearing():
    d = schedule_player(with_sax_lead(), "bass")
    assert d.interaction is InteractionKind.LOCK
    assert d.target_player_ids == ("sax",)


def test_drums_support_active_leader():
    d = schedule_player(with_sax_lead(), "drums")
    assert d.interaction is InteractionKind.SUPPORT


def test_phrase_ending_creates_setup_and_answer_window():
    s = with_sax_lead(phrase_maturity=.88)
    drums = schedule_player(s, "drums")
    piano = schedule_player(s, "piano")
    assert drums.interaction is InteractionKind.SETUP
    assert piano.interaction is InteractionKind.ANSWER
    assert "phrase_handoff_window" in drums.tags


def test_no_leader_allows_designated_soloist_to_lead():
    d = schedule_player(state(), "sax")
    assert d.interaction is InteractionKind.LEAD
    assert d.leadership_delta > 0


def test_crowded_ensemble_reduces_competing_density():
    s = state()
    for pid, role in (
        ("sax", InteractionKind.LEAD),
        ("piano", InteractionKind.BUILD),
        ("drums", InteractionKind.BUILD),
        ("bass", InteractionKind.LOCK),
    ):
        s = update_player_intent(s, PlayerActionIntent(
            pid, role, density=.95, energy=.8,
            leadership=.9 if pid == "sax" else .1,
        ))
    d = schedule_player(s, "piano")
    assert d.density_delta < 0
    assert "ensemble_crowded" in d.tags


def test_form_boundary_gives_drums_transition_and_bass_lock():
    s = state(form_position=.98)
    assert schedule_player(s, "drums").interaction is InteractionKind.TRANSITION
    assert schedule_player(s, "bass").interaction is InteractionKind.LOCK


def test_all_players_are_scheduled_from_same_snapshot():
    directives = schedule_ensemble(with_sax_lead())
    assert {d.player_id for d in directives} == {"piano", "bass", "drums", "sax"}


def test_directive_projects_to_provisional_intent_without_notes():
    s = with_sax_lead()
    directive = schedule_player(s, "piano")
    intent = directive_to_intent(directive, previous=s.intent_for("piano"))
    assert intent.player_id == "piano"
    assert not hasattr(intent, "future_notes")
    assert not hasattr(intent, "midi_notes")
    assert not hasattr(intent, "voicing")
