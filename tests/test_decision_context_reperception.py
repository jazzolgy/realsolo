from music_intelligence.reasoning.decision_context_log import (
    CandidateAudit,
    DecisionContextLog,
    DecisionRecord,
    PostEventObservation,
    extract_prior_components,
    snapshot_ensemble_context,
)
from music_intelligence.reasoning.ensemble_state import (
    CommitmentState,
    EnsembleObservation,
    EnsembleState,
    InteractionEvent,
    InteractionKind,
    PlayerActionIntent,
    PlayerPresence,
    PlayerRole,
    TransportState,
    reperceive_ensemble_state,
)


def _state():
    return EnsembleState(
        transport=TransportState(
            beat=8.0,
            bar=3,
            section="A",
            chorus=1,
            form_position=.25,
        ),
        players=(
            PlayerPresence("piano","piano",PlayerRole.COMPER),
            PlayerPresence("bass","bass",PlayerRole.BASS),
            PlayerPresence("drums","drum_set",PlayerRole.DRUMS),
        ),
        ensemble_density=.4,
        ensemble_energy=.5,
        ensemble_tension=.35,
        space_available=.55,
    )


def test_decision_log_preserves_context_candidates_and_prior_contributions():
    state=_state()
    snapshot=snapshot_ensemble_context(state)
    record=DecisionRecord(
        decision_id="decision:1",
        player_id="piano",
        decision_kind="comping",
        context=snapshot,
        candidates=(
            CandidateAudit("silence",.25,{"ensemble_space":.16}),
            CandidateAudit(
                "punctuate",
                .31,
                {
                    "phrase_space_fit":.24,
                    "learned_comping:style:comping_density_mean":.02,
                },
            ),
        ),
        selected_candidate_id="punctuate",
        selected_score=.31,
        prior_contributions={
            "learned_comping:style:comping_density_mean":.02,
        },
        contextual_gate_weights={"domain":.7,"genre":.2,"style":.3,"legend":.4},
        provenance=("piano_comping_evaluator",),
    )
    log=DecisionContextLog()
    log.append_decision(record)

    assert log.decisions[0].context.generation == 0
    assert log.decisions[0].selected_candidate_id == "punctuate"


def test_reperception_updates_next_shared_state_without_quality_judgment():
    state=_state()
    observation=EnsembleObservation(
        ensemble_density=.7,
        ensemble_energy=.65,
        space_available=.3,
        observed_intents=(
            PlayerActionIntent(
                player_id="drums",
                interaction=InteractionKind.SETUP,
                commitment=CommitmentState.PLAYED,
                density=.8,
                energy=.7,
            ),
        ),
        observed_interactions=(
            InteractionEvent(
                source_player_id="drums",
                kind=InteractionKind.SETUP,
                confidence=.9,
            ),
        ),
    )

    updated=reperceive_ensemble_state(state,observation)

    assert updated.ensemble_density == .7
    assert updated.ensemble_energy == .65
    assert updated.space_available == .3
    assert updated.intent_for("drums").interaction is InteractionKind.SETUP
    assert updated.recent_interactions[-1].kind is InteractionKind.SETUP
    assert updated.generation > state.generation


def test_post_event_observation_is_linked_but_does_not_create_feedback():
    state=_state()
    log=DecisionContextLog()
    log.append_decision(
        DecisionRecord(
            decision_id="decision:1",
            player_id="piano",
            decision_kind="solo",
            context=snapshot_ensemble_context(state),
            candidates=(CandidateAudit("note:60",.4),),
            selected_candidate_id="note:60",
            selected_score=.4,
        )
    )
    after=reperceive_ensemble_state(
        state,
        EnsembleObservation(ensemble_density=.6),
    )
    log.append_post_event_observation(
        PostEventObservation(
            decision_id="decision:1",
            context=snapshot_ensemble_context(after),
            observed_event_ids=("event:drums:1",),
        )
    )

    observation=log.observations_for("decision:1")[0]
    assert observation.context.ensemble_density == .6
    assert not hasattr(observation,"success")
    assert not hasattr(observation,"reward")


def test_extract_prior_components_keeps_prior_terms_only():
    selected=extract_prior_components({
        "harmonic_identity":.28,
        "legend:passing":.1,
        "learned_solo_entry_phase":.04,
        "learned_comping:genre:comping_density_mean":.02,
    })
    assert set(selected)=={
        "legend:passing",
        "learned_solo_entry_phase",
        "learned_comping:genre:comping_density_mean",
    }
