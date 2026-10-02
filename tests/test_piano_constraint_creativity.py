from dataclasses import replace

from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import (
    CompingPriority,
    CompingRoleOccupancy,
    ConstraintAwarePianoCompingEvaluator,
    DimensionContinuityProfile,
    PianoCompingContext,
    PianoCompingState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    build_contextual_comping_candidates,
)
from players.piano.constraint_creativity import adapt_profile_for_ensemble_context


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


def test_busy_solo_redirects_freedom_to_expression_axes():
    base = DimensionContinuityProfile(
        role=0.6,
        family=0.6,
        rhythm=0.6,
        register=0.6,
        dynamic=0.6,
        touch=0.6,
    )
    adapted = adapt_profile_for_ensemble_context(
        base,
        PianoCompingContext(
            soloist_activity=0.95,
            ensemble_density=0.4,
        ),
    )
    assert adapted.dynamic < base.dynamic
    assert adapted.touch < base.touch
    assert adapted.register < base.register
    assert adapted.family == base.family


def test_phrase_space_makes_role_and_timing_more_changeable():
    base = DimensionContinuityProfile()
    adapted = adapt_profile_for_ensemble_context(
        base,
        PianoCompingContext(
            phrase_boundary_probability=0.95,
            available_space_beats=1.5,
        ),
    )
    assert adapted.role < base.role
    assert adapted.rhythm < base.rhythm


def test_other_primary_moves_creativity_away_from_harmonic_duplication():
    base = DimensionContinuityProfile(
        role=0.5,
        family=0.4,
        rhythm=0.5,
        register=0.5,
        dynamic=0.5,
        touch=0.5,
    )
    adapted = adapt_profile_for_ensemble_context(
        base,
        PianoCompingContext(
            role_occupancy=CompingRoleOccupancy(
                priority=CompingPriority.OTHER_PRIMARY,
                other_comping_activity=0.9,
                other_harmonic_coverage=0.9,
                other_rhythmic_coverage=0.8,
            )
        ),
    )
    assert adapted.family >= base.family
    assert adapted.rhythm < base.rhythm
    assert adapted.touch < base.touch
    assert adapted.register < base.register


def test_harmonic_disagreement_constrains_family_but_not_global_creativity():
    base = DimensionContinuityProfile(
        role=0.5,
        family=0.4,
        rhythm=0.5,
        register=0.5,
        dynamic=0.5,
        touch=0.5,
    )
    adapted = adapt_profile_for_ensemble_context(
        base,
        PianoCompingContext(
            role_occupancy=CompingRoleOccupancy(
                priority=CompingPriority.SHARED,
                other_harmonic_coverage=0.7,
                harmonic_agreement_confidence=0.15,
            )
        ),
    )
    assert adapted.family > base.family
    assert adapted.dynamic < base.dynamic
    assert adapted.touch < base.touch


def test_constraint_aware_evaluator_applies_creative_correction():
    ctx = PianoCompingContext(
        soloist_activity=0.9,
        ensemble_density=0.82,
        creativity_strength=1.0,
    )
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(material()),
        ctx,
    )
    original = next(c for c in slate.candidates if c.realization is not None)

    state = PianoCompingState()
    state.commit(original, section_energy=0.5)

    varied = replace(
        original,
        tags=frozenset(
            {t for t in original.tags if not t.startswith(("register:", "dynamic:", "touch:"))}
            | {"register:higher", "dynamic:soft", "touch:neutral"}
        ),
    )

    score = ConstraintAwarePianoCompingEvaluator().evaluate(
        varied,
        ctx,
        MusicalContextVector(ensemble_activity=0.8),
        state,
    )
    assert "constraint_creativity_adjustment" in score.components
    assert score.components["constraint_creativity_adjustment"] != 0


def test_constrained_silence_is_not_forced_to_be_novel():
    ctx = PianoCompingContext(
        soloist_activity=0.95,
        ensemble_density=0.9,
        creativity_strength=1.0,
    )
    slate = build_contextual_comping_candidates(
        PianoVoicingRequest(material()),
        ctx,
    )
    silence = next(c for c in slate.candidates if c.realization is None)

    state = PianoCompingState()
    state.commit(silence, section_energy=0.5)

    score = ConstraintAwarePianoCompingEvaluator().evaluate(
        silence,
        ctx,
        MusicalContextVector(ensemble_activity=0.9),
        state,
    )
    assert score.components.get("constraint_creativity_adjustment", 0) == 0
