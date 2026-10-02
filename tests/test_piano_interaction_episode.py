from dataclasses import replace

from music_intelligence.harmony.jazz_harmony_core import HarmonicAffordance, HarmonicIntent
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import (
    CompingActionType,
    EnsembleActor,
    EnsembleResponseObservation,
    InteractionEpisodeType,
    InteractionRole,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    ResponseType,
    build_immediate_performance_candidates,
    evaluate_episode_bias,
    infer_interaction_episode,
)


def material():
    return ResolvedHarmonicMaterial(
        affordance_id="dominant.altered_color",
        root_pitch_class=7,
        role_pitch_classes={
            "root": (7,),
            "3rd": (11,),
            "b7": (5,),
            "b9": (8,),
            "#9": (10,),
            "b13": (3,),
        },
    )


def affordance():
    return HarmonicAffordance(
        affordance_id="dominant.altered_color",
        intent=HarmonicIntent.INTENSIFY,
        harmonic_role="altered_dominant",
    )


def slate(ctx, state):
    return build_immediate_performance_candidates(
        PianoVoicingRequest(material(), high_midi=84),
        ctx,
        state.interaction_state_from_context(ctx),
        affordance(),
    )


def first_sounding(ctx, state):
    return next(c for c in slate(ctx, state).candidates if c.realization is not None)


def test_two_response_turns_can_form_open_dialogue_episode():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.8,
        available_space_beats=1.0,
        drummer_activity=0.8,
        section_energy=0.6,
    )

    g1 = first_sounding(ctx, state)
    state.commit(g1, section_energy=0.6)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.DRUMMER,
            ResponseType.RHYTHMIC_ECHO,
            strength=1.0,
            confidence=1.0,
            attribution_confidence=0.8,
        )
    )

    g2 = first_sounding(ctx, state)
    state.commit(g2, section_energy=0.6)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.SOLOIST,
            ResponseType.SPACE_OPENED,
            strength=0.8,
            confidence=0.9,
            attribution_confidence=0.7,
        )
    )

    assert state.active_episode is not None
    assert state.active_episode.episode_type is InteractionEpisodeType.OPEN_DIALOGUE
    assert len(state.active_episode.turns) == 2


def test_soloist_phrase_extension_forms_soloist_lead_episode():
    state = PianoCompingState()
    ctx = PianoCompingContext(section_energy=0.6)
    g = first_sounding(ctx, state)
    state.commit(g, section_energy=0.6)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.SOLOIST,
            ResponseType.PHRASE_EXTENSION,
            strength=1.0,
            confidence=0.95,
            attribution_confidence=0.8,
        )
    )

    assert state.active_episode is not None
    assert state.active_episode.episode_type is InteractionEpisodeType.SOLOIST_LEAD


def test_density_response_forms_density_shift_episode():
    state = PianoCompingState()
    ctx = PianoCompingContext(section_energy=0.6)
    g = first_sounding(ctx, state)
    state.commit(g, section_energy=0.6)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.ENSEMBLE,
            ResponseType.DENSITY_INCREASE,
            strength=0.9,
            confidence=0.9,
            attribution_confidence=0.7,
        )
    )
    assert state.active_episode.episode_type is InteractionEpisodeType.DENSITY_SHIFT


def test_open_dialogue_biases_answer_or_punctuation():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        drummer_activity=0.8,
        section_energy=0.6,
    )
    g1 = first_sounding(ctx, state)
    state.commit(g1, section_energy=0.6)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.DRUMMER,
            ResponseType.RHYTHMIC_ECHO,
            strength=1.0,
            confidence=1.0,
            attribution_confidence=0.9,
        )
    )
    g2 = first_sounding(ctx, state)
    state.commit(g2, section_energy=0.6)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.SOLOIST,
            ResponseType.SPACE_OPENED,
            strength=1.0,
            confidence=1.0,
            attribution_confidence=0.9,
        )
    )

    answer = next(
        c for c in slate(ctx, state).candidates
        if c.role is InteractionRole.ANSWER and c.realization is not None
    )
    score = evaluate_episode_bias(answer, state.active_episode)
    assert score.components.get("dialogue_turn", 0) > 0


def test_soloist_lead_biases_lay_out_over_build():
    state = PianoCompingState()
    ctx = PianoCompingContext(section_energy=0.7)
    g = first_sounding(ctx, state)
    state.commit(g, section_energy=0.7)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.SOLOIST,
            ResponseType.PHRASE_EXTENSION,
            strength=1.0,
            confidence=1.0,
            attribution_confidence=1.0,
        )
    )

    current = slate(ctx, state).candidates
    silence = next(c for c in current if c.action_type is CompingActionType.SILENCE)
    build = next(c for c in current if c.role is InteractionRole.BUILD and c.realization is not None)

    a = evaluate_episode_bias(silence, state.active_episode)
    b = evaluate_episode_bias(build, state.active_episode)
    assert a.total > b.total


def test_episode_bias_is_used_by_comping_evaluator():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        section_energy=0.6,
    )
    g1 = first_sounding(ctx, state)
    state.commit(g1, section_energy=0.6)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.DRUMMER,
            ResponseType.RHYTHMIC_ECHO,
            strength=1.0,
            confidence=1.0,
            attribution_confidence=1.0,
        )
    )
    g2 = first_sounding(ctx, state)
    state.commit(g2, section_energy=0.6)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.SOLOIST,
            ResponseType.SPACE_OPENED,
            strength=1.0,
            confidence=1.0,
            attribution_confidence=1.0,
        )
    )
    answer = next(
        c for c in slate(ctx, state).candidates
        if c.role is InteractionRole.ANSWER and c.realization is not None
    )

    score = PianoCompingEvaluator().evaluate(
        answer,
        ctx,
        MusicalContextVector(ensemble_activity=0.4),
        state,
        affordance(),
        state.interaction_state_from_context(ctx),
    )
    assert score.components.get("interaction_episode:dialogue_turn", 0) > 0


def test_episode_uses_only_recent_observed_turns():
    state = PianoCompingState()
    ctx = PianoCompingContext(section_energy=0.5)
    for _ in range(6):
        g = first_sounding(ctx, state)
        state.commit(g, section_energy=0.5)
        state.record_ensemble_response(
            EnsembleResponseObservation(
                EnsembleActor.ENSEMBLE,
                ResponseType.DENSITY_DECREASE,
                confidence=0.8,
                attribution_confidence=0.5,
            )
        )

    episode = infer_interaction_episode(state.recent_responses, max_turns=4)
    assert episode is not None
    assert len(episode.turns) == 4


def test_episode_contains_no_future_actions():
    state = PianoCompingState()
    ctx = PianoCompingContext(section_energy=0.5)
    g = first_sounding(ctx, state)
    state.commit(g, section_energy=0.5)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.SOLOIST,
            ResponseType.PHRASE_EXTENSION,
        )
    )

    assert state.active_episode is not None
    assert not hasattr(state.active_episode, "future_actions")
    assert not hasattr(state.active_episode, "next_gesture")
    assert not hasattr(state.active_episode, "planned_sequence")


def test_episode_deactivates_after_two_no_clear_response_turns():
    state = PianoCompingState()
    ctx = PianoCompingContext(section_energy=0.5)

    for response_type in (
        ResponseType.RHYTHMIC_ECHO,
        ResponseType.NO_CLEAR_RESPONSE,
        ResponseType.NO_CLEAR_RESPONSE,
    ):
        g = first_sounding(ctx, state)
        state.commit(g, section_energy=0.5)
        state.record_ensemble_response(
            EnsembleResponseObservation(
                EnsembleActor.ENSEMBLE,
                response_type,
                confidence=0.8,
                attribution_confidence=0.5,
            )
        )

    assert state.active_episode is not None
    assert state.active_episode.active is False


def test_inactive_episode_has_no_policy_bias():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        section_energy=0.5,
    )
    for response_type in (
        ResponseType.RHYTHMIC_ECHO,
        ResponseType.NO_CLEAR_RESPONSE,
        ResponseType.NO_CLEAR_RESPONSE,
    ):
        g = first_sounding(ctx, state)
        state.commit(g, section_energy=0.5)
        state.record_ensemble_response(
            EnsembleResponseObservation(
                EnsembleActor.ENSEMBLE,
                response_type,
                confidence=1.0,
                attribution_confidence=1.0,
            )
        )

    answer = next(
        c for c in slate(ctx, state).candidates
        if c.role is InteractionRole.ANSWER and c.realization is not None
    )
    score = evaluate_episode_bias(answer, state.active_episode)
    assert score.total == 0.0
