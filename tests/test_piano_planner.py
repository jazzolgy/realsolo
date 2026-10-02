from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicAffordance,
    HarmonicIntent,
)
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import (
    CompingActionType,
    InteractionRole,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    build_contextual_comping_candidates,
)


def dominant_material():
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


def test_candidate_factory_keeps_silence_in_every_slate():
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(dominant_material()),
        PianoCompingContext(),
        affordance(),
    )
    assert any(c.action_type is CompingActionType.SILENCE for c in slate.candidates)


def test_candidate_factory_contains_shell_support():
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(dominant_material()),
        PianoCompingContext(soloist_activity=0.8, ensemble_density=0.7),
        affordance(),
    )
    assert any(
        c.role is InteractionRole.SUPPORT
        and c.realization is not None
        and "shell" in c.realization.event.tags
        for c in slate.candidates
    )


def test_phrase_space_enables_rootless_response_candidates():
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(dominant_material()),
        PianoCompingContext(
            soloist_activity=0.2,
            phrase_boundary_probability=0.9,
            available_space_beats=1.0,
            ensemble_density=0.3,
        ),
        affordance(),
    )
    assert any(
        c.role is InteractionRole.ANSWER
        and c.realization is not None
        and "rootless" in c.realization.event.tags
        for c in slate.candidates
    )


def test_low_phrase_space_does_not_generate_response_candidate():
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(dominant_material()),
        PianoCompingContext(
            soloist_activity=0.9,
            phrase_boundary_probability=0.1,
            available_space_beats=0.0,
            ensemble_density=0.8,
        ),
        affordance(),
    )
    assert not any(c.role is InteractionRole.ANSWER for c in slate.candidates)


def test_busy_context_selects_silence_or_shell_not_rootless_answer():
    ctx = PianoCompingContext(
        soloist_activity=0.95,
        phrase_boundary_probability=0.1,
        available_space_beats=0.0,
        ensemble_density=0.85,
        recent_piano_density=0.8,
        section_energy=0.45,
    )
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(dominant_material()),
        ctx,
        affordance(),
    )
    chosen = PianoCompingEvaluator().choose_immediate(
        slate.candidates,
        ctx,
        MusicalContextVector(chord_symbol="G7", ensemble_activity=0.9),
        PianoCompingState(),
        affordance(),
    )
    assert chosen.candidate.role in {InteractionRole.LAY_OUT, InteractionRole.SUPPORT}
    assert chosen.candidate.role is not InteractionRole.ANSWER


def test_open_phrase_space_can_select_rootless_answer():
    ctx = PianoCompingContext(
        soloist_activity=0.15,
        phrase_boundary_probability=0.95,
        available_space_beats=1.5,
        ensemble_density=0.25,
        recent_piano_density=0.2,
        section_energy=0.55,
    )
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(dominant_material()),
        ctx,
        affordance(),
    )
    chosen = PianoCompingEvaluator().choose_immediate(
        slate.candidates,
        ctx,
        MusicalContextVector(chord_symbol="G7", ensemble_activity=0.25),
        PianoCompingState(),
        affordance(),
    )
    assert chosen.candidate.role is InteractionRole.ANSWER
    assert chosen.candidate.realization is not None
    assert "rootless" in chosen.candidate.realization.event.tags


def test_candidate_factory_does_not_freeze_future_sequence():
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(dominant_material()),
        PianoCompingContext(),
        affordance(),
    )
    assert not any(hasattr(c, "future_sequence") for c in slate.candidates)
