from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicAffordance,
    HarmonicIntent,
)
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import (
    CompingActionType,
    EnergyDirection,
    InteractionRole,
    PhraseSpaceWindow,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoDensity,
    PianoInteractionState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    build_contextual_comping_candidates,
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


def slate(ctx):
    return build_contextual_comping_candidates(
        PianoVoicingRequest(modal_material(), high_midi=84),
        ctx,
        modal_affordance(),
    )


def test_rising_energy_biases_build_over_same_candidate_without_narrative():
    ctx = PianoCompingContext(
        soloist_activity=0.2,
        phrase_boundary_probability=0.7,
        available_space_beats=1.0,
        ensemble_density=0.35,
        section_energy=0.8,
    )
    candidates = slate(ctx).candidates
    build = next(c for c in candidates if c.role is InteractionRole.BUILD)

    ev = PianoCompingEvaluator()
    base = ev.evaluate(
        build,
        ctx,
        MusicalContextVector(ensemble_activity=0.35),
        PianoCompingState(),
        modal_affordance(),
    )
    rising = ev.evaluate(
        build,
        ctx,
        MusicalContextVector(ensemble_activity=0.35),
        PianoCompingState(),
        modal_affordance(),
        PianoInteractionState(
            soloist_activity=0.2,
            ensemble_density=0.35,
            section_energy=0.8,
            energy_direction=EnergyDirection.UP,
        ),
    )
    assert rising.total > base.total


def test_falling_energy_penalizes_build_and_rewards_lay_out():
    ctx = PianoCompingContext(
        soloist_activity=0.25,
        phrase_boundary_probability=0.2,
        available_space_beats=0.0,
        ensemble_density=0.35,
        section_energy=0.7,
    )
    candidates = slate(ctx).candidates
    build = next(c for c in candidates if c.role is InteractionRole.BUILD)
    silence = next(c for c in candidates if c.action_type is CompingActionType.SILENCE)

    interaction = PianoInteractionState(
        soloist_activity=0.25,
        ensemble_density=0.35,
        section_energy=0.7,
        energy_direction=EnergyDirection.DOWN,
    )
    ev = PianoCompingEvaluator()
    build_score = ev.evaluate(
        build,
        ctx,
        MusicalContextVector(ensemble_activity=0.35),
        PianoCompingState(),
        modal_affordance(),
        interaction,
    )
    silence_score = ev.evaluate(
        silence,
        ctx,
        MusicalContextVector(ensemble_activity=0.35),
        PianoCompingState(),
        modal_affordance(),
        interaction,
    )
    assert silence_score.total > build_score.total


def test_recent_high_piano_density_increases_recovery_space_bias():
    ctx = PianoCompingContext(
        soloist_activity=0.45,
        ensemble_density=0.55,
        section_energy=0.55,
    )
    silence = next(c for c in slate(ctx).candidates if c.action_type is CompingActionType.SILENCE)

    ev = PianoCompingEvaluator()
    low = ev.evaluate(
        silence,
        ctx,
        MusicalContextVector(ensemble_activity=0.55),
        PianoCompingState(),
        modal_affordance(),
        PianoInteractionState(
            soloist_activity=0.45,
            ensemble_density=0.55,
            recent_piano_density=PianoDensity(voice_count=1, onset_rate=0.2),
        ),
    )
    high = ev.evaluate(
        silence,
        ctx,
        MusicalContextVector(ensemble_activity=0.55),
        PianoCompingState(),
        modal_affordance(),
        PianoInteractionState(
            soloist_activity=0.45,
            ensemble_density=0.55,
            recent_piano_density=PianoDensity(
                voice_count=6,
                onset_rate=4.0,
                sustain_ratio=0.9,
                register_span=36,
                registral_concentration=0.9,
                dynamic_weight=0.9,
                pedal_blur=0.8,
            ),
        ),
    )
    assert high.total > low.total


def test_phrase_space_biases_answer_without_preplanning_notes():
    ctx = PianoCompingContext(
        soloist_activity=0.15,
        phrase_boundary_probability=0.95,
        available_space_beats=1.5,
        ensemble_density=0.25,
        section_energy=0.55,
    )
    answer = next(c for c in slate(ctx).candidates if c.role is InteractionRole.ANSWER)

    score = PianoCompingEvaluator().evaluate(
        answer,
        ctx,
        MusicalContextVector(ensemble_activity=0.25),
        PianoCompingState(),
        modal_affordance(),
        PianoInteractionState(
            soloist_activity=0.15,
            ensemble_density=0.25,
            phrase_space=PhraseSpaceWindow(
                confidence=0.95,
                estimated_length_beats=1.5,
                source="solo_phrase_boundary",
            ),
            section_energy=0.55,
            energy_direction=EnergyDirection.STABLE,
        ),
    )

    assert score.components["narrative:phrase_space_fit"] > 0
    assert not hasattr(answer, "next_action")
    assert not hasattr(answer, "future_family")


def test_narrative_bias_can_change_family_preference_without_fixed_sequence():
    ctx = PianoCompingContext(
        soloist_activity=0.2,
        phrase_boundary_probability=0.7,
        available_space_beats=1.0,
        ensemble_density=0.35,
        section_energy=0.8,
    )
    candidates = slate(ctx).candidates
    evaluator = PianoCompingEvaluator()

    rising = evaluator.choose_immediate(
        candidates,
        ctx,
        MusicalContextVector(ensemble_activity=0.35),
        PianoCompingState(),
        modal_affordance(),
        PianoInteractionState(
            soloist_activity=0.2,
            ensemble_density=0.35,
            section_energy=0.8,
            energy_direction=EnergyDirection.UP,
        ),
    )

    falling = evaluator.choose_immediate(
        candidates,
        ctx,
        MusicalContextVector(ensemble_activity=0.35),
        PianoCompingState(),
        modal_affordance(),
        PianoInteractionState(
            soloist_activity=0.2,
            ensemble_density=0.35,
            section_energy=0.8,
            energy_direction=EnergyDirection.DOWN,
        ),
    )

    assert rising.candidate.role in {
        InteractionRole.BUILD,
        InteractionRole.ANSWER,
        InteractionRole.PUNCTUATE,
        InteractionRole.SUPPORT,
        InteractionRole.ANCHOR,
    }
    assert falling.candidate.role is not InteractionRole.BUILD
