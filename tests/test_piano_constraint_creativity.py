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
        },
    )


def test_busy_context_keeps_expression_axes_available():
    base=DimensionContinuityProfile(
        role=.6,family=.6,rhythm=.6,register=.6,dynamic=.6,touch=.6
    )
    out=adapt_profile_for_ensemble_context(
        base,
        PianoCompingContext(soloist_activity=.95,ensemble_density=.85),
    )
    assert out.register < base.register
    assert out.dynamic < base.dynamic
    assert out.touch < base.touch


def test_other_primary_moves_freedom_away_from_harmonic_duplication():
    base=DimensionContinuityProfile(
        role=.5,family=.4,rhythm=.5,register=.5,dynamic=.5,touch=.5
    )
    out=adapt_profile_for_ensemble_context(
        base,
        PianoCompingContext(
            role_occupancy=CompingRoleOccupancy(
                priority=CompingPriority.OTHER_PRIMARY,
                other_harmonic_coverage=.9,
                other_rhythmic_coverage=.8,
            )
        ),
    )
    assert out.family >= base.family
    assert out.rhythm < base.rhythm
    assert out.register < base.register
    assert out.touch < base.touch


def test_constraint_evaluator_corrects_creativity_with_expression_complete_history():
    ctx=PianoCompingContext(
        soloist_activity=.9,
        ensemble_density=.82,
        creativity_strength=1.0,
    )
    slate=build_contextual_comping_candidates(
        PianoVoicingRequest(material()),
        ctx,
    )
    original=next(c for c in slate.candidates if c.realization is not None)
    original=replace(
        original,
        tags=frozenset(
            set(original.tags)
            | {"register:stay","dynamic:medium","touch:neutral"}
        ),
    )

    state=PianoCompingState()
    state.commit(original,section_energy=.5)

    varied=replace(
        original,
        tags=frozenset(
            {t for t in original.tags if not t.startswith(("register:","dynamic:","touch:"))}
            | {"register:higher","dynamic:soft","touch:legato"}
        ),
    )

    score=ConstraintAwarePianoCompingEvaluator().evaluate(
        varied,
        ctx,
        MusicalContextVector(ensemble_activity=.8),
        state,
    )
    assert "constraint_creativity_adjustment" in score.components
    assert score.components["constraint_creativity_adjustment"] != 0


def test_silence_is_not_forced_into_novelty():
    ctx=PianoCompingContext(
        soloist_activity=.95,
        ensemble_density=.9,
        creativity_strength=1.0,
    )
    slate=build_contextual_comping_candidates(
        PianoVoicingRequest(material()),
        ctx,
    )
    silence=next(c for c in slate.candidates if c.realization is None)
    state=PianoCompingState()
    state.commit(silence,section_energy=.5)

    score=ConstraintAwarePianoCompingEvaluator().evaluate(
        silence,
        ctx,
        MusicalContextVector(ensemble_activity=.9),
        state,
    )
    assert score.components.get("constraint_creativity_adjustment",0) == 0
