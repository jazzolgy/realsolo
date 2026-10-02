from music_intelligence.harmony.jazz_harmony_core import HarmonicAffordance, HarmonicIntent
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import (
    DynamicLevel,
    EnergyDirection,
    InteractionRole,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoInteractionState,
    PianoVoicingRequest,
    RegisterDirection,
    ResolvedHarmonicMaterial,
    TouchType,
    build_contextual_comping_candidates,
    expand_candidate_set_expressively,
    expression_intents_for_candidate,
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


def interaction(direction=EnergyDirection.STABLE, solo=0.3, density=0.4):
    return PianoInteractionState(
        soloist_activity=solo,
        ensemble_density=density,
        section_energy=0.6,
        energy_direction=direction,
    )


def first_sounding(ctx):
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(material(), high_midi=84),
        ctx,
        affordance(),
    )
    return next(c for c in slate.candidates if c.realization is not None)


def test_rising_energy_exposes_higher_stronger_expression_option():
    c = first_sounding(PianoCompingContext(section_energy=0.7))
    intents = expression_intents_for_candidate(
        c,
        interaction(EnergyDirection.UP),
    )
    assert any(
        x.register_direction is RegisterDirection.HIGHER
        and x.dynamic_level is DynamicLevel.STRONG
        for x in intents
    )


def test_falling_energy_exposes_soft_expression_option():
    c = first_sounding(PianoCompingContext(section_energy=0.4))
    intents = expression_intents_for_candidate(
        c,
        interaction(EnergyDirection.DOWN),
    )
    assert any(x.dynamic_level is DynamicLevel.SOFT for x in intents)


def test_active_bass_exposes_higher_register_option():
    c = first_sounding(PianoCompingContext(bass_activity=0.9))
    intents = expression_intents_for_candidate(
        c,
        interaction(),
        bass_activity=0.9,
    )
    assert any(x.register_direction is RegisterDirection.HIGHER for x in intents)


def test_expression_expansion_preserves_pitch_classes():
    ctx = PianoCompingContext(section_energy=0.7)
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(material(), high_midi=84),
        ctx,
        affordance(),
    )
    base = next(c for c in slate.candidates if c.realization is not None)
    original_pcs = tuple(v.pitch_midi % 12 for v in base.realization.event.voices)

    expanded = expand_candidate_set_expressively(
        type(slate)((base,)),
        ctx,
        interaction(EnergyDirection.UP),
    )
    assert len(expanded.candidates) >= 2
    for c in expanded.candidates:
        assert tuple(v.pitch_midi % 12 for v in c.realization.event.voices) == original_pcs


def test_soloist_register_overlap_creates_separation_option():
    ctx = PianoCompingContext(
        soloist_register_midi=62,
        section_energy=0.5,
    )
    c = first_sounding(ctx)
    center = sum(c.realization.event.pitches_midi) / len(c.realization.event.pitches_midi)
    intents = expression_intents_for_candidate(
        c,
        interaction(),
        soloist_register_midi=center,
    )
    assert any(x.dynamic_level is DynamicLevel.SOFT for x in intents)
    assert any(x.register_direction is not RegisterDirection.STAY for x in intents)


def test_busy_ensemble_penalizes_strong_and_rewards_soft_expression():
    ctx = PianoCompingContext(
        soloist_activity=0.9,
        ensemble_density=0.85,
        section_energy=0.7,
    )
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(material(), high_midi=84),
        ctx,
        affordance(),
    )
    base = next(c for c in slate.candidates if c.realization is not None)
    variants = expand_candidate_set_expressively(
        type(slate)((base,)),
        ctx,
        interaction(EnergyDirection.UP, solo=0.9, density=0.85),
    ).candidates
    soft = next(c for c in variants if "dynamic:soft" in c.tags)
    strong = next(c for c in variants if "dynamic:strong" in c.tags)

    ev = PianoCompingEvaluator()
    a = ev.evaluate(
        soft, ctx, MusicalContextVector(ensemble_activity=0.9),
        PianoCompingState(), affordance(), interaction(EnergyDirection.UP, solo=0.9, density=0.85)
    )
    b = ev.evaluate(
        strong, ctx, MusicalContextVector(ensemble_activity=0.9),
        PianoCompingState(), affordance(), interaction(EnergyDirection.UP, solo=0.9, density=0.85)
    )
    assert a.total > b.total


def test_expression_variants_do_not_encode_future_trajectory():
    ctx = PianoCompingContext(section_energy=0.7)
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(material(), high_midi=84),
        ctx,
        affordance(),
    )
    base = next(c for c in slate.candidates if c.realization is not None)
    variants = expand_candidate_set_expressively(
        type(slate)((base,)), ctx, interaction(EnergyDirection.UP)
    ).candidates
    assert all(not hasattr(c, "future_registers") for c in variants)
    assert all(not hasattr(c, "future_dynamics") for c in variants)
