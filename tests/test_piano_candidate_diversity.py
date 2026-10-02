from music_intelligence.harmony.jazz_harmony_core import HarmonicAffordance, HarmonicIntent
from players.piano import (
    EnergyDirection,
    PianoCompingContext,
    PianoInteractionState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    build_immediate_performance_candidates,
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


def test_small_candidate_cap_preserves_multiple_voicing_families():
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        drummer_activity=0.8,
        section_energy=0.8,
    )
    interaction = PianoInteractionState(
        soloist_activity=0.2,
        ensemble_density=0.35,
        section_energy=0.8,
        energy_direction=EnergyDirection.UP,
    )
    slate = build_immediate_performance_candidates(
        PianoVoicingRequest(modal_material(), high_midi=84),
        ctx,
        interaction,
        modal_affordance(),
        max_candidates=12,
    )

    families = {
        c.realization.event.source_family
        for c in slate.candidates
        if c.realization is not None
    }
    assert len(slate.candidates) <= 12
    assert len(families) >= 3


def test_small_candidate_cap_preserves_timing_and_expression_diversity():
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        drummer_activity=0.9,
        section_energy=0.8,
    )
    interaction = PianoInteractionState(
        soloist_activity=0.2,
        ensemble_density=0.35,
        section_energy=0.8,
        energy_direction=EnergyDirection.UP,
    )
    slate = build_immediate_performance_candidates(
        PianoVoicingRequest(modal_material(), high_midi=84),
        ctx,
        interaction,
        modal_affordance(),
        max_candidates=20,
    )

    rhythm_tags = {
        tag
        for c in slate.candidates
        for tag in c.tags
        if tag.startswith("rhythm:")
    }
    dynamic_tags = {
        tag
        for c in slate.candidates
        for tag in c.tags
        if tag.startswith("dynamic:")
    }
    register_tags = {
        tag
        for c in slate.candidates
        for tag in c.tags
        if tag.startswith("register:")
    }

    assert len(rhythm_tags) >= 2
    assert len(dynamic_tags) >= 2
    assert len(register_tags) >= 2


def test_diversity_pruning_still_preserves_silence():
    slate = build_immediate_performance_candidates(
        PianoVoicingRequest(modal_material(), high_midi=84),
        PianoCompingContext(section_energy=0.8),
        PianoInteractionState(section_energy=0.8),
        modal_affordance(),
        max_candidates=6,
    )
    assert slate.silent
