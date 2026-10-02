from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicAffordance,
    HarmonicIntent,
)
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from music_intelligence.reasoning.online_improviser import SoftPlan
from players.piano import (
    CompingActionType,
    InteractionRole,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    build_contextual_comping_candidates,
    perform_one_comping_action,
)


def modal_material():
    return ResolvedHarmonicMaterial(
        affordance_id="modal.static_color",
        root_pitch_class=7,
        role_pitch_classes={
            "root": (7,),
            "3rd": (11,),
            "b7": (5,),
            "9": (9,),
            "11": (0,),
            "13": (4,),
        },
    )


def modal_affordance():
    return HarmonicAffordance(
        affordance_id="modal.static_color",
        intent=HarmonicIntent.COLOR,
        harmonic_role="modal_color",
        context_tags=frozenset({"modal", "static_harmony"}),
    )


def make_slate(ctx):
    return build_contextual_comping_candidates(
        PianoVoicingRequest(modal_material(), high_midi=84),
        ctx,
        modal_affordance(),
    )


def test_committed_sounding_gesture_updates_recent_density_memory():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        soloist_activity=0.2,
        phrase_boundary_probability=0.8,
        available_space_beats=1.0,
        ensemble_density=0.3,
        section_energy=0.8,
    )
    candidate = next(
        c for c in make_slate(ctx).candidates
        if c.realization is not None and c.role is InteractionRole.BUILD
    )

    state.commit(candidate, section_energy=ctx.section_energy)

    assert state.recent_density.voice_count > 0
    assert state.recent_density.intrusion_index > 0
    assert state.sounding_streak == 1
    assert state.silence_streak == 0
    assert state.last_family is not None
    assert state.last_role == "build"


def test_silence_decays_recent_density_and_resets_sounding_streak():
    state = PianoCompingState()
    busy_ctx = PianoCompingContext(section_energy=0.8)
    sounding = next(
        c for c in make_slate(busy_ctx).candidates
        if c.realization is not None and c.role is InteractionRole.BUILD
    )
    silence = next(
        c for c in make_slate(busy_ctx).candidates
        if c.action_type is CompingActionType.SILENCE
    )

    state.commit(sounding, section_energy=0.8)
    before = state.recent_density.intrusion_index
    state.commit(silence, section_energy=0.7)
    after = state.recent_density.intrusion_index

    assert after < before
    assert state.sounding_streak == 0
    assert state.silence_streak == 1
    assert state.last_family is None


def test_interaction_state_infers_energy_direction_from_previous_tick():
    state = PianoCompingState()

    initial_ctx = PianoCompingContext(section_energy=0.4)
    silence = next(
        c for c in make_slate(initial_ctx).candidates
        if c.action_type is CompingActionType.SILENCE
    )
    state.commit(silence, section_energy=0.4)

    rising = state.interaction_state_from_context(
        PianoCompingContext(section_energy=0.65)
    )
    falling = state.interaction_state_from_context(
        PianoCompingContext(section_energy=0.2)
    )

    assert rising.energy_direction.value == "up"
    assert falling.energy_direction.value == "down"


def test_runtime_automatically_uses_memory_without_explicit_interaction_state():
    state = PianoCompingState()
    ctx1 = PianoCompingContext(
        soloist_activity=0.2,
        phrase_boundary_probability=0.8,
        available_space_beats=1.0,
        ensemble_density=0.3,
        section_energy=0.75,
    )
    slate1 = make_slate(ctx1)
    perform_one_comping_action(
        SoftPlan(2, "build current texture"),
        PianoCompingEvaluator(),
        slate1.candidates,
        ctx1,
        MusicalContextVector(ensemble_activity=0.3),
        state,
        modal_affordance(),
    )

    assert len(state.committed) == 1
    assert state.last_section_energy == 0.75

    ctx2 = PianoCompingContext(
        soloist_activity=0.3,
        phrase_boundary_probability=0.2,
        available_space_beats=0.0,
        ensemble_density=0.45,
        section_energy=0.45,
    )
    inferred = state.interaction_state_from_context(ctx2)
    assert inferred.energy_direction.value == "down"
    assert inferred.recent_piano_density == state.recent_density


def test_feedback_loop_still_commits_only_one_immediate_action_per_tick():
    state = PianoCompingState()
    ctx = PianoCompingContext(
        soloist_activity=0.2,
        phrase_boundary_probability=0.8,
        available_space_beats=1.0,
        ensemble_density=0.3,
        section_energy=0.7,
    )
    slate = make_slate(ctx)

    perform_one_comping_action(
        SoftPlan(4, "respond"),
        PianoCompingEvaluator(),
        slate.candidates,
        ctx,
        MusicalContextVector(ensemble_activity=0.3),
        state,
        modal_affordance(),
    )

    assert len(state.committed) == 1
    assert not hasattr(state, "future_actions")
    assert not hasattr(state, "future_voicings")
