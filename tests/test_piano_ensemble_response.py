from dataclasses import replace

import pytest

from music_intelligence.harmony.jazz_harmony_core import HarmonicAffordance, HarmonicIntent
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import (
    CompingActionType,
    EnsembleActor,
    EnsembleResponseObservation,
    InteractionRole,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    ResponseType,
    build_immediate_performance_candidates,
    evaluate_response_bias,
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


def test_response_cannot_be_attributed_before_any_piano_gesture():
    state = PianoCompingState()
    with pytest.raises(ValueError):
        state.record_ensemble_response(
            EnsembleResponseObservation(
                EnsembleActor.DRUMMER,
                ResponseType.RHYTHMIC_ECHO,
            )
        )


def test_response_memory_links_observation_to_last_committed_gesture():
    state = PianoCompingState()
    ctx = PianoCompingContext(section_energy=0.5)
    gesture = first_sounding(ctx, state)
    state.commit(gesture, section_energy=0.5)

    observation = EnsembleResponseObservation(
        EnsembleActor.DRUMMER,
        ResponseType.RHYTHMIC_ECHO,
        strength=0.8,
        latency_beats=0.5,
        confidence=0.9,
        attribution_confidence=0.7,
        provenance=("synthetic_test",),
    )
    state.record_ensemble_response(observation)

    record = state.recent_responses[-1]
    assert record.gesture == state.recent_signatures[-1]
    assert record.observation == observation


def test_drummer_echo_rewards_same_rhythm_without_requiring_exact_gesture():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.7,
        available_space_beats=1.0,
        drummer_activity=0.8,
        section_energy=0.6,
    )
    candidates = [c for c in slate(ctx, state).candidates if c.realization is not None]
    original = next(c for c in candidates if any(t.startswith("rhythm:") for t in c.tags))
    state.commit(original, section_energy=0.6)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.DRUMMER,
            ResponseType.RHYTHMIC_ECHO,
            strength=1.0,
            confidence=1.0,
            attribution_confidence=1.0,
        )
    )

    rhythm = next(t for t in original.tags if t.startswith("rhythm:"))
    varied = replace(
        original,
        tags=frozenset(
            {t for t in original.tags if not t.startswith("register:")}
            | {"register:higher"}
        ),
    )
    assert rhythm in varied.tags

    score = evaluate_response_bias(varied, state.recent_responses)
    assert score.components.get("responsive_groove_continuity", 0) > 0


def test_soloist_phrase_extension_rewards_space_and_penalizes_build():
    state = PianoCompingState()
    ctx = PianoCompingContext(section_energy=0.7)
    gesture = first_sounding(ctx, state)
    state.commit(gesture, section_energy=0.7)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.SOLOIST,
            ResponseType.PHRASE_EXTENSION,
            strength=1.0,
            confidence=1.0,
            attribution_confidence=0.9,
        )
    )

    current = slate(ctx, state).candidates
    silence = next(c for c in current if c.action_type is CompingActionType.SILENCE)
    build = next(
        c for c in current
        if c.role is InteractionRole.BUILD and c.realization is not None
    )

    a = evaluate_response_bias(silence, state.recent_responses)
    b = evaluate_response_bias(build, state.recent_responses)
    assert a.total > b.total


def test_space_opened_rewards_answer_or_fill():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        section_energy=0.6,
    )
    gesture = first_sounding(ctx, state)
    state.commit(gesture, section_energy=0.6)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.SOLOIST,
            ResponseType.SPACE_OPENED,
            strength=0.9,
            confidence=0.9,
            attribution_confidence=0.8,
        )
    )

    answer = next(
        c for c in slate(ctx, state).candidates
        if c.role is InteractionRole.ANSWER and c.realization is not None
    )
    score = evaluate_response_bias(answer, state.recent_responses)
    assert score.components.get("response_window", 0) > 0


def test_density_increase_favors_recovery_space():
    state = PianoCompingState()
    ctx = PianoCompingContext(section_energy=0.7)
    gesture = first_sounding(ctx, state)
    state.commit(gesture, section_energy=0.7)
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.ENSEMBLE,
            ResponseType.DENSITY_INCREASE,
            strength=1.0,
            confidence=0.9,
            attribution_confidence=0.8,
        )
    )

    current = slate(ctx, state).candidates
    silence = next(c for c in current if c.action_type is CompingActionType.SILENCE)
    score = evaluate_response_bias(silence, state.recent_responses)
    assert score.components.get("density_recovery", 0) > 0


def test_low_attribution_confidence_has_small_effect():
    state = PianoCompingState()
    ctx = PianoCompingContext(section_energy=0.5)
    gesture = first_sounding(ctx, state)
    state.commit(gesture, section_energy=0.5)

    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.DRUMMER,
            ResponseType.RHYTHMIC_ECHO,
            strength=1.0,
            confidence=1.0,
            attribution_confidence=0.05,
        )
    )
    current = replace(
        gesture,
        tags=frozenset(
            {t for t in gesture.tags if not t.startswith("register:")}
            | {"register:higher"}
        ),
    )
    weak = evaluate_response_bias(current, state.recent_responses)

    state.recent_responses.clear()
    state.record_ensemble_response(
        EnsembleResponseObservation(
            EnsembleActor.DRUMMER,
            ResponseType.RHYTHMIC_ECHO,
            strength=1.0,
            confidence=1.0,
            attribution_confidence=1.0,
        )
    )
    strong = evaluate_response_bias(current, state.recent_responses)
    assert weak.total < strong.total


def test_comping_evaluator_consumes_response_memory():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        section_energy=0.6,
    )
    gesture = first_sounding(ctx, state)
    state.commit(gesture, section_energy=0.6)
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
    assert score.components.get("ensemble_response:response_window", 0) > 0


def test_response_memory_is_bounded_and_contains_no_future_plan():
    state = PianoCompingState()
    ctx = PianoCompingContext(section_energy=0.5)
    gesture = first_sounding(ctx, state)
    state.commit(gesture, section_energy=0.5)

    for _ in range(20):
        state.record_ensemble_response(
            EnsembleResponseObservation(
                EnsembleActor.ENSEMBLE,
                ResponseType.NO_CLEAR_RESPONSE,
            )
        )

    assert len(state.recent_responses) == 8
    assert all(not hasattr(x, "future_actions") for x in state.recent_responses)
    assert all(not hasattr(x, "future_sequence") for x in state.recent_responses)


def test_coarse_context_transition_detects_density_increase_with_low_attribution():
    state = PianoCompingState()
    before = PianoCompingContext(
        soloist_activity=0.3,
        phrase_boundary_probability=0.2,
        available_space_beats=0.0,
        ensemble_density=0.3,
        section_energy=0.5,
    )
    gesture = first_sounding(before, state)
    state.commit(gesture, section_energy=0.5)

    after = PianoCompingContext(
        soloist_activity=0.35,
        phrase_boundary_probability=0.25,
        available_space_beats=0.0,
        ensemble_density=0.7,
        section_energy=0.6,
    )
    observations = state.observe_context_transition(before, after)
    assert any(x.response_type is ResponseType.DENSITY_INCREASE for x in observations)
    assert all(x.attribution_confidence == pytest.approx(0.25) for x in observations)


def test_coarse_context_transition_detects_space_opening():
    state = PianoCompingState()
    before = PianoCompingContext(
        soloist_activity=0.6,
        phrase_boundary_probability=0.2,
        available_space_beats=0.0,
        ensemble_density=0.5,
    )
    gesture = first_sounding(before, state)
    state.commit(gesture, section_energy=0.5)

    after = PianoCompingContext(
        soloist_activity=0.2,
        phrase_boundary_probability=0.85,
        available_space_beats=1.0,
        ensemble_density=0.35,
    )
    observations = state.observe_context_transition(before, after)
    assert any(x.response_type is ResponseType.SPACE_OPENED for x in observations)


def test_coarse_transition_does_not_invent_rhythmic_echo_from_scalar_context():
    state = PianoCompingState()
    before = PianoCompingContext(
        soloist_activity=0.3,
        ensemble_density=0.4,
    )
    gesture = first_sounding(before, state)
    state.commit(gesture, section_energy=0.5)

    after = PianoCompingContext(
        soloist_activity=0.3,
        ensemble_density=0.4,
    )
    observations = state.observe_context_transition(before, after)
    assert not any(x.response_type is ResponseType.RHYTHMIC_ECHO for x in observations)


def test_context_transition_observations_feed_next_tick_bias():
    state = PianoCompingState()
    before = PianoCompingContext(
        soloist_activity=0.3,
        ensemble_density=0.3,
        section_energy=0.5,
    )
    gesture = first_sounding(before, state)
    state.commit(gesture, section_energy=0.5)

    after = PianoCompingContext(
        soloist_activity=0.35,
        ensemble_density=0.75,
        section_energy=0.6,
    )
    state.observe_context_transition(
        before,
        after,
        attribution_confidence=0.5,
    )

    silence = next(
        c for c in slate(after, state).candidates
        if c.action_type is CompingActionType.SILENCE
    )
    score = evaluate_response_bias(silence, state.recent_responses)
    assert score.components.get("density_recovery", 0) > 0
