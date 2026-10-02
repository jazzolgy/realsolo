from music_intelligence.reasoning.ensemble_state import (
    CommitmentState,
    EnsembleState,
    InteractionEvent,
    InteractionKind,
    PlayerActionIntent,
    PlayerPresence,
    PlayerRole,
    TransportState,
    append_interaction,
    player_view,
    update_player_intent,
)


def base_state():
    return EnsembleState(
        transport=TransportState(beat=1.0, bar=0, section="A"),
        players=(
            PlayerPresence("piano", "piano", PlayerRole.COMPER),
            PlayerPresence("bass", "bass", PlayerRole.BASS),
            PlayerPresence("drums", "drums", PlayerRole.DRUMS),
            PlayerPresence("sax", "tenor_sax", PlayerRole.SOLOIST),
        ),
    )


def test_all_players_read_same_shared_state_with_self_filtered_view():
    state = update_player_intent(base_state(), PlayerActionIntent(
        "sax", InteractionKind.LEAD, density=.8, leadership=.9
    ))
    piano = player_view(state, "piano")
    bass = player_view(state, "bass")
    assert piano.ensemble_density == bass.ensemble_density
    assert any(i.player_id == "sax" for i in piano.other_intents)


def test_sax_leadership_becomes_shared_leader_signal():
    state = update_player_intent(base_state(), PlayerActionIntent(
        "sax", InteractionKind.LEAD, leadership=.92, density=.72, energy=.8
    ))
    assert state.leader_player_id == "sax"
    assert state.ensemble_energy > .0


def test_space_request_and_density_reduce_available_space():
    state = base_state()
    state = update_player_intent(state, PlayerActionIntent(
        "sax", InteractionKind.LEAD, density=.8, space_request=.5
    ))
    crowded = state.space_available
    state = update_player_intent(state, PlayerActionIntent(
        "piano", InteractionKind.YIELD, density=.15, space_request=.0
    ))
    assert state.space_available > crowded


def test_committed_intent_can_be_shared_without_future_notes():
    intent = PlayerActionIntent(
        "bass",
        InteractionKind.LOCK,
        commitment=CommitmentState.COMMITTED,
        density=.5,
        tags=frozenset({"walking", "quarter_note_pulse"}),
        decision_time=1.0,
        commit_time=1.01,
    )
    assert not hasattr(intent, "future_notes")
    assert not hasattr(intent, "future_chords")
    assert not hasattr(intent, "midi_notes")


def test_interaction_history_is_bounded_and_non_destructive():
    state = base_state()
    for n in range(40):
        state = append_interaction(state, InteractionEvent(
            "drums", InteractionKind.PUNCTUATE, beat=float(n)
        ), history_limit=8)
    assert len(state.recent_interactions) == 8
    assert state.recent_interactions[-1].beat == 39.0


def test_unknown_player_intent_is_rejected():
    state = base_state()
    try:
        update_player_intent(state, PlayerActionIntent("guitar", InteractionKind.LEAD))
    except ValueError as e:
        assert "unknown player" in str(e)
    else:
        raise AssertionError("expected unknown-player validation error")
