import dataclasses

from music_intelligence.learning.engine import LearningPriorView
from music_intelligence.learning.representation import LearningDomain
from music_intelligence.reasoning.contextual_prior_gating import PriorGatingContext
from music_intelligence.reasoning.hierarchical_priors import (
    HierarchicalPriorSet,
    PriorLayerWeights,
)
from music_intelligence.reasoning.legend_style_core import (
    LegendBlend,
    LegendProfile,
    StyleTendency,
)
from music_intelligence.reasoning.motif.evaluator import MotifEvaluation
from music_intelligence.reasoning.motif.policy import MotifPolicyDecision
from music_intelligence.reasoning.motif.representation import (
    MotifCandidate,
    MotifIdentity,
    MotifSourceType,
)
from music_intelligence.reasoning.musical_policy_projection import (
    MusicalPolicyAxis,
    project_musical_policy,
)
from music_intelligence.reasoning.solo_grammar import SoloDevelopmentOperation


def prior(features):
    return LearningPriorView(
        domain=LearningDomain.SOLO_PHRASE,
        numeric_features=features,
        categorical_counts={},
        feedback_bias={},
        observations=4,
        numeric_weights={k: 2.0 for k in features},
        categorical_weights={},
        weighted_observations=2.0,
    )


def motif_decision(operation):
    candidate=MotifCandidate(
        identity=MotifIdentity(
            motif_id="test.motif",
            contour="rising",
            provenance=("test_motif",),
        ),
        source_type=MotifSourceType.SELF_MEMORY_DERIVED,
        generation_weight=.6,
    )
    evaluation=MotifEvaluation(
        total=.75,
        identity_clarity=.6,
        rhythmic_salience=.5,
        harmonic_flexibility=.7,
        transformability=.7,
        memorability=.6,
        interaction_potential=.5,
        redundancy_penalty=0.0,
    )
    return MotifPolicyDecision(
        candidate=candidate,
        evaluation=evaluation,
        development_operation=operation,
    )


def test_projection_uses_only_canonical_learning_features():
    p=prior({
        "policy.space": .9,
        "onset_rate_p50": 4.2,
    })
    out=project_musical_policy(
        priors=HierarchicalPriorSet(domain_prior=p),
    )
    assert out.space_bias > 0
    assert all("onset_rate_p50" not in x.reason for x in out.contributions)


def test_contextual_gating_attenuates_projection_without_reimplementing_gate():
    p=prior({"policy.motif_repeat": .9})
    base=HierarchicalPriorSet(
        domain_prior=p,
        weights=PriorLayerWeights(domain=1.0,genre=0.0,style=0.0,legend=0.0),
    )
    open_out=project_musical_policy(priors=base)
    gated_out=project_musical_policy(
        priors=base,
        gating_context=PriorGatingContext(
            ensemble_complexity=1.0,
            live_context_confidence=1.0,
            structural_constraint=1.0,
        ),
    )
    assert 0 < gated_out.motif_repeat_bias < open_out.motif_repeat_bias
    assert "contextual_prior_gating" in gated_out.provenance


def test_legend_and_motif_are_normalized_into_same_policy_language():
    legend=LegendProfile(
        profile_id="legend.test",
        display_name="test",
        instrument_family="bass",
        era_or_school="test",
        tendencies=(
            StyleTendency(
                "t1",
                "solo.rhythmic_displacement",
                context_tags=frozenset({"solo","develop"}),
                weight=.2,
                confidence=.8,
            ),
        ),
    )
    priors=HierarchicalPriorSet(
        legend_blend=LegendBlend(((legend,1.0),)),
        weights=PriorLayerWeights(domain=0.0,genre=0.0,style=0.0,legend=1.0),
    )
    out=project_musical_policy(
        priors=priors,
        motif_decision=motif_decision(SoloDevelopmentOperation.DISPLACE),
        active_tags=("solo","develop"),
    )
    assert out.rhythmic_displacement_bias > 0
    assert {x.source for x in out.contributions} == {"legend","motif_policy"}
    assert out.axis_value(MusicalPolicyAxis.RHYTHMIC_DISPLACEMENT) == out.rhythmic_displacement_bias


def test_projection_contract_contains_no_player_realization_commands():
    fields={x.name for x in dataclasses.fields(
        __import__(
            "music_intelligence.reasoning.musical_policy_projection",
            fromlist=["MusicalPolicyProjection"],
        ).MusicalPolicyProjection
    )}
    forbidden={
        "pitch_midi","pitch_class","voicing","string","fret","limb",
        "ride_hit","snare_hit","kick_hit","render_event",
    }
    assert not fields & forbidden


def test_motif_decision_is_exposed_not_redecided():
    decision=motif_decision(SoloDevelopmentOperation.REPEAT)
    out=project_musical_policy(motif_decision=decision)
    assert out.motif_repeat_bias > 0
    assert out.motif_variation_bias == 0
    assert any("selected repeat" in x.reason for x in out.contributions)
