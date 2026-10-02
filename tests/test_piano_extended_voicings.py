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
    generate_extended_voicing_families,
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


def functional_affordance():
    return HarmonicAffordance(
        affordance_id="modal.static_color",
        intent=HarmonicIntent.CONNECT,
        harmonic_role="voice_leading",
        context_tags=frozenset(),
    )


def test_extended_generators_cover_mcneely_study_families():
    candidates = generate_extended_voicing_families(
        PianoVoicingRequest(modal_material(), low_midi=43, high_midi=84)
    )
    families = {candidate.event.source_family for candidate in candidates}
    assert "piano_tertian" in families
    assert "piano_quartal" in families
    assert "piano_inverted_quartal" in families
    assert "piano_octave" in families
    assert "piano_mixed" in families


def test_extended_family_generator_uses_only_supplied_pitch_classes():
    request = PianoVoicingRequest(modal_material(), low_midi=43, high_midi=84)
    supplied = {
        pc
        for pcs in request.material.role_pitch_classes.values()
        for pc in pcs
    }
    for candidate in generate_extended_voicing_families(request):
        assert all(v.pitch_midi % 12 in supplied for v in candidate.event.voices)


def test_extended_families_are_not_added_without_static_modal_context():
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(modal_material(), high_midi=84),
        PianoCompingContext(section_energy=0.8),
        functional_affordance(),
    )
    assert not any("extended_family" in c.tags for c in slate.candidates)


def test_static_modal_context_adds_extended_family_candidates():
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(modal_material(), high_midi=84),
        PianoCompingContext(section_energy=0.8),
        modal_affordance(),
    )
    families = {
        c.realization.event.source_family
        for c in slate.candidates
        if c.realization is not None and "extended_family" in c.tags
    }
    assert "piano_quartal" in families
    assert "piano_inverted_quartal" in families
    assert "piano_octave" in families
    assert "piano_tertian" in families
    assert "piano_mixed" in families


def test_high_energy_static_context_includes_build_or_punctuate_roles():
    ctx = PianoCompingContext(
        soloist_activity=0.25,
        phrase_boundary_probability=0.7,
        available_space_beats=1.0,
        ensemble_density=0.4,
        section_energy=0.85,
    )
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(modal_material(), high_midi=84),
        ctx,
        modal_affordance(),
    )
    extended = [c for c in slate.candidates if "extended_family" in c.tags]
    assert any(c.role is InteractionRole.BUILD for c in extended)
    assert any(
        c.role in {InteractionRole.PUNCTUATE, InteractionRole.SUPPORT}
        for c in extended
    )


def test_extended_candidates_remain_immediate_gestures_not_future_progressions():
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(modal_material(), high_midi=84),
        PianoCompingContext(section_energy=0.7),
        modal_affordance(),
    )
    for candidate in slate.candidates:
        assert not hasattr(candidate, "future_voicings")
        assert not hasattr(candidate, "future_sequence")


def test_busy_solo_can_still_choose_silence_even_when_modal_families_exist():
    ctx = PianoCompingContext(
        soloist_activity=0.95,
        phrase_boundary_probability=0.1,
        available_space_beats=0.0,
        ensemble_density=0.9,
        recent_piano_density=0.8,
        section_energy=0.8,
    )
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(modal_material(), high_midi=84),
        ctx,
        modal_affordance(),
    )
    chosen = PianoCompingEvaluator().choose_immediate(
        slate.candidates,
        ctx,
        MusicalContextVector(ensemble_activity=0.9),
        PianoCompingState(),
        modal_affordance(),
    )
    assert chosen.candidate.action_type is CompingActionType.SILENCE
