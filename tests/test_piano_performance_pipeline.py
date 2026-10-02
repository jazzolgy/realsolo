from music_intelligence.harmony.jazz_harmony_core import HarmonicAffordance, HarmonicIntent
from players.piano import (
    EnergyDirection,
    PianoCompingContext,
    PianoInteractionState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    build_immediate_performance_candidates,
)


def material():
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


def affordance():
    return HarmonicAffordance(
        affordance_id="modal.static_color",
        intent=HarmonicIntent.COLOR,
        harmonic_role="modal_color",
        context_tags=frozenset({"modal", "static_harmony"}),
    )


def test_full_pipeline_contains_rhythm_and_expression_variants():
    ctx = PianoCompingContext(
        soloist_activity=0.2,
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        drummer_activity=0.8,
        ensemble_density=0.35,
        section_energy=0.75,
        soloist_register_midi=67,
    )
    interaction = PianoInteractionState(
        soloist_activity=0.2,
        ensemble_density=0.35,
        section_energy=0.75,
        energy_direction=EnergyDirection.UP,
    )
    slate = build_immediate_performance_candidates(
        PianoVoicingRequest(material(), high_midi=84),
        ctx,
        interaction,
        affordance(),
    )
    sounding = [c for c in slate.candidates if c.realization is not None]
    assert sounding
    assert any(any(t.startswith("rhythm:") for t in c.tags) for c in sounding)
    assert any(any(t.startswith("dynamic:") for t in c.tags) for c in sounding)
    assert any(any(t.startswith("register:") for t in c.tags) for c in sounding)


def test_full_pipeline_preserves_silence():
    slate = build_immediate_performance_candidates(
        PianoVoicingRequest(material(), high_midi=84),
        PianoCompingContext(),
        PianoInteractionState(),
        affordance(),
    )
    assert slate.silent


def test_full_pipeline_respects_candidate_cap():
    slate = build_immediate_performance_candidates(
        PianoVoicingRequest(material(), high_midi=84),
        PianoCompingContext(
            phrase_boundary_probability=0.9,
            available_space_beats=1.0,
            drummer_activity=0.9,
            section_energy=0.8,
        ),
        PianoInteractionState(
            section_energy=0.8,
            energy_direction=EnergyDirection.UP,
        ),
        affordance(),
        max_candidates=20,
    )
    assert len(slate.candidates) <= 20
    assert slate.silent


def test_pipeline_can_disable_expansion_stages_for_ablation():
    base = build_immediate_performance_candidates(
        PianoVoicingRequest(material(), high_midi=84),
        PianoCompingContext(),
        PianoInteractionState(),
        affordance(),
        include_rhythm=False,
        include_expression=False,
    )
    assert all(
        not any(tag.startswith("rhythm:") for tag in c.tags)
        for c in base.candidates
    )
    assert all(
        not any(tag.startswith("dynamic:") for tag in c.tags)
        for c in base.candidates
    )


def test_pipeline_never_contains_future_sequence_fields():
    slate = build_immediate_performance_candidates(
        PianoVoicingRequest(material(), high_midi=84),
        PianoCompingContext(section_energy=0.7),
        PianoInteractionState(
            section_energy=0.7,
            energy_direction=EnergyDirection.UP,
        ),
        affordance(),
    )
    for c in slate.candidates:
        assert not hasattr(c, "future_sequence")
        assert not hasattr(c, "future_actions")
        assert not hasattr(c, "future_voicings")
