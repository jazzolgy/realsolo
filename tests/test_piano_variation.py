from dataclasses import replace

from music_intelligence.harmony.jazz_harmony_core import HarmonicAffordance, HarmonicIntent
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import (
    CompingActionType,
    InteractionRole,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    VariationContext,
    build_immediate_performance_candidates,
    evaluate_variation,
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
    interaction = state.interaction_state_from_context(ctx)
    return build_immediate_performance_candidates(
        PianoVoicingRequest(material(), high_midi=84),
        ctx,
        interaction,
        affordance(),
    )


def test_exact_recent_signature_is_penalized():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.8,
        available_space_beats=1.0,
        section_energy=0.6,
        variation_pressure=1.0,
    )
    candidates = slate(ctx, state).candidates
    first = next(c for c in candidates if c.realization is not None)
    state.commit(first, section_energy=0.6)

    score = evaluate_variation(
        first,
        state.recent_signatures,
        VariationContext(variation_pressure=1.0),
    )
    assert score.total < 0
    assert score.components["exact_repetition"] < 0


def test_partial_variation_can_score_above_exact_repeat():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.8,
        available_space_beats=1.0,
        section_energy=0.6,
        variation_pressure=1.0,
    )
    candidates = [c for c in slate(ctx, state).candidates if c.realization is not None]
    original = candidates[0]
    state.commit(original, section_energy=0.6)

    varied = replace(
        original,
        tags=frozenset(set(original.tags) | {"rhythm:offbeat"}),
    )

    exact_score = evaluate_variation(
        original,
        state.recent_signatures,
        VariationContext(variation_pressure=1.0),
    )
    varied_score = evaluate_variation(
        varied,
        state.recent_signatures,
        VariationContext(variation_pressure=1.0),
    )
    assert varied_score.total > exact_score.total


def test_groove_lock_can_reward_same_rhythm_with_other_changes():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        drummer_activity=0.8,
        section_energy=0.7,
    )
    candidates = [c for c in slate(ctx, state).candidates if c.realization is not None]
    original = next(c for c in candidates if any(t.startswith("rhythm:") for t in c.tags))
    state.commit(original, section_energy=0.7)

    rhythm_tag = next(t for t in original.tags if t.startswith("rhythm:"))
    varied = next(
        c for c in candidates
        if c is not original
        and rhythm_tag in c.tags
        and (
            c.realization.event.source_family != original.realization.event.source_family
            or c.role != original.role
            or c.tags != original.tags
        )
    )

    score = evaluate_variation(
        varied,
        state.recent_signatures,
        VariationContext(
            variation_pressure=0.7,
            groove_lock_strength=1.0,
        ),
    )
    assert score.components.get("groove_continuity", 0) > 0


def test_motif_continuity_can_reward_same_family_role_with_changed_realization():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        section_energy=0.7,
    )
    candidates = [c for c in slate(ctx, state).candidates if c.realization is not None]
    original = candidates[0]
    state.commit(original, section_energy=0.7)

    varied = replace(
        original,
        tags=frozenset(set(original.tags) | {"register:higher"}),
    )

    score = evaluate_variation(
        varied,
        state.recent_signatures,
        VariationContext(
            variation_pressure=0.5,
            motif_continuity_strength=1.0,
        ),
    )
    assert score.components.get("motif_continuity", 0) > 0


def test_repetition_streak_increases_change_pressure():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.5,
        section_energy=0.5,
        variation_pressure=1.0,
    )
    candidate = next(c for c in slate(ctx, state).candidates if c.realization is not None)
    state.commit(candidate, section_energy=0.5)
    state.commit(candidate, section_energy=0.5)

    score = evaluate_variation(
        candidate,
        state.recent_signatures,
        VariationContext(variation_pressure=1.0),
    )
    assert score.components.get("repetition_streak", 0) < 0


def test_comping_evaluator_uses_recent_signature_memory():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.8,
        available_space_beats=1.0,
        section_energy=0.6,
        variation_pressure=1.0,
    )
    candidates = [c for c in slate(ctx, state).candidates if c.realization is not None]
    original = candidates[0]
    state.commit(original, section_energy=0.6)

    varied = replace(
        original,
        tags=frozenset(set(original.tags) | {"rhythm:offbeat"}),
    )

    ev = PianoCompingEvaluator()
    exact = ev.evaluate(
        original,
        ctx,
        MusicalContextVector(ensemble_activity=0.4),
        state,
        affordance(),
        state.interaction_state_from_context(ctx),
    )
    alternative = ev.evaluate(
        varied,
        ctx,
        MusicalContextVector(ensemble_activity=0.4),
        state,
        affordance(),
        state.interaction_state_from_context(ctx),
    )
    assert alternative.total > exact.total


def test_silence_signature_is_remembered_as_musical_action():
    state = PianoCompingState()
    silence = next(
        c for c in slate(PianoCompingContext(), state).candidates
        if c.action_type is CompingActionType.SILENCE
    )
    state.commit(silence, section_energy=0.5)

    assert state.recent_signatures
    assert state.recent_signatures[-1].role == InteractionRole.LAY_OUT.value
    assert state.recent_signatures[-1].family is None


def test_signature_memory_is_bounded():
    state = PianoCompingState()
    ctx = PianoCompingContext()
    silence = next(c for c in slate(ctx, state).candidates if c.action_type is CompingActionType.SILENCE)

    for _ in range(20):
        state.commit(silence, section_energy=0.5)

    assert len(state.recent_signatures) == 8


def test_variation_memory_does_not_store_future_gestures():
    state = PianoCompingState()
    ctx = PianoCompingContext()
    candidate = next(c for c in slate(ctx, state).candidates if c.realization is not None)
    state.commit(candidate, section_energy=0.5)

    assert all(not hasattr(sig, "future_sequence") for sig in state.recent_signatures)
    assert all(not hasattr(sig, "next_gesture") for sig in state.recent_signatures)
