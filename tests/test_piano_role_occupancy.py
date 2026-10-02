from music_intelligence.harmony.jazz_harmony_core import HarmonicAffordance, HarmonicIntent
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import (
    CompingActionType,
    CompingPriority,
    CompingRoleOccupancy,
    InteractionRole,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    build_immediate_performance_candidates,
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


def slate(ctx):
    state=PianoCompingState()
    return build_immediate_performance_candidates(
        PianoVoicingRequest(material(), high_midi=84),
        ctx,
        state.interaction_state_from_context(ctx),
        affordance(),
    )


def test_other_primary_rewards_space_and_sparse_secondary_comping():
    ctx=PianoCompingContext(
        role_occupancy=CompingRoleOccupancy(
            priority=CompingPriority.OTHER_PRIMARY,
            other_comping_activity=0.9,
            other_harmonic_coverage=0.9,
            other_rhythmic_coverage=0.8,
        )
    )
    candidates=slate(ctx).candidates
    silence=next(c for c in candidates if c.action_type is CompingActionType.SILENCE)
    sparse=next(c for c in candidates if c.action_type is CompingActionType.SPARSE_SUPPORT)

    ev=PianoCompingEvaluator()
    s=ev.evaluate(silence,ctx,MusicalContextVector(),PianoCompingState(),affordance())
    p=ev.evaluate(sparse,ctx,MusicalContextVector(),PianoCompingState(),affordance())

    assert s.components.get("role_occupancy:yield_to_primary",0)>0
    assert p.components.get("role_occupancy:secondary_sparse_fit",0)>0


def test_other_primary_penalizes_sustained_duplicate_harmony():
    ctx=PianoCompingContext(
        section_energy=0.8,
        role_occupancy=CompingRoleOccupancy(
            priority=CompingPriority.OTHER_PRIMARY,
            other_comping_activity=0.9,
            other_harmonic_coverage=0.95,
        ),
    )
    sustained=next(
        c for c in slate(ctx).candidates
        if c.action_type is CompingActionType.SUSTAINED_SUPPORT
    )
    score=PianoCompingEvaluator().evaluate(
        sustained,ctx,MusicalContextVector(),PianoCompingState(),affordance()
    )
    assert score.components.get("role_occupancy:harmonic_coverage_conflict",0)<0


def test_piano_primary_support_is_not_treated_as_partner_conflict():
    ctx=PianoCompingContext(
        role_occupancy=CompingRoleOccupancy(
            priority=CompingPriority.PIANO_PRIMARY,
            other_comping_activity=0.1,
            other_harmonic_coverage=0.1,
        )
    )
    support=next(
        c for c in slate(ctx).candidates
        if c.role is InteractionRole.SUPPORT and c.realization is not None
    )
    score=PianoCompingEvaluator().evaluate(
        support,ctx,MusicalContextVector(),PianoCompingState(),affordance()
    )
    assert score.components.get("role_occupancy:primary_support_fit",0)>0


def test_shared_high_coverage_penalizes_dense_or_sustained_comping():
    ctx=PianoCompingContext(
        section_energy=0.8,
        role_occupancy=CompingRoleOccupancy(
            priority=CompingPriority.SHARED,
            other_comping_activity=0.9,
            other_harmonic_coverage=0.8,
        )
    )
    sustained=next(
        c for c in slate(ctx).candidates
        if c.action_type is CompingActionType.SUSTAINED_SUPPORT
    )
    score=PianoCompingEvaluator().evaluate(
        sustained,ctx,MusicalContextVector(),PianoCompingState(),affordance()
    )
    assert score.components.get("role_occupancy:shared_density_conflict",0)<0


def test_low_harmonic_agreement_confidence_penalizes_sounding_candidates():
    ctx=PianoCompingContext(
        role_occupancy=CompingRoleOccupancy(
            priority=CompingPriority.SHARED,
            other_comping_activity=0.6,
            other_harmonic_coverage=0.6,
            harmonic_agreement_confidence=0.2,
        )
    )
    sounding=next(c for c in slate(ctx).candidates if c.realization is not None)
    score=PianoCompingEvaluator().evaluate(
        sounding,ctx,MusicalContextVector(),PianoCompingState(),affordance()
    )
    assert score.components.get("role_occupancy:harmonic_disagreement_risk",0)<0


def test_role_occupancy_contains_no_future_schedule():
    occ=CompingRoleOccupancy(
        priority=CompingPriority.OTHER_PRIMARY,
        other_comping_activity=0.8,
        other_harmonic_coverage=0.8,
    )
    assert not hasattr(occ,"future_turns")
    assert not hasattr(occ,"next_primary")
