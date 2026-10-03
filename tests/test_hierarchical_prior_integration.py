import pytest

from music_intelligence.learning import LearningDomain, LearningPriorView
from music_intelligence.reasoning.hierarchical_priors import (
    HierarchicalPriorSet,
    PriorLayerWeights,
)
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano.comping import (
    CompingActionType,
    InteractionRole,
    PianoCompingCandidate,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
)
from players.piano.solo import PianoSoloEvaluator


def _prior(domain, feature, value, weight=1.0):
    return LearningPriorView(
        domain=domain,
        numeric_features={feature: value},
        categorical_counts={},
        feedback_bias={},
        observations=1,
        numeric_weights={feature: weight},
        categorical_weights={},
        weighted_observations=weight,
    )


def test_comping_hierarchy_combines_domain_genre_and_style_layers():
    hierarchy = HierarchicalPriorSet(
        domain_prior=_prior(LearningDomain.COMPING, "density", 0.0),
        genre_prior=_prior(LearningDomain.GENRE, "comping_density_mean", 0.0),
        style_prior=_prior(LearningDomain.STYLE, "comping_density_mean", 0.0),
        weights=PriorLayerWeights(domain=1.0, genre=.45, style=.60, legend=1.0),
    )
    candidate = PianoCompingCandidate(
        action_type=CompingActionType.SILENCE,
        role=InteractionRole.LAY_OUT,
        duration_beats=1.0,
    )
    context = PianoCompingContext()
    musical = MusicalContextVector()
    state = PianoCompingState()

    domain_only = PianoCompingEvaluator(
        comping_prior=hierarchy.domain_prior
    ).evaluate(candidate, context, musical, state)
    layered = PianoCompingEvaluator(
        prior_hierarchy=hierarchy
    ).evaluate(candidate, context, musical, state)

    assert layered.total > domain_only.total
    assert "learned_comping:domain:density" in layered.components
    assert "learned_comping:genre:comping_density_mean" in layered.components
    assert "learned_comping:style:comping_density_mean" in layered.components


def test_explicit_legend_blend_still_has_priority_over_hierarchy_legend():
    # Constructor precedence is part of the API contract: an explicitly chosen
    # legend blend remains authoritative over a bundle default.
    explicit = PianoSoloEvaluator().legend_blend
    hierarchy = HierarchicalPriorSet(legend_blend=explicit)
    evaluator = PianoSoloEvaluator(
        legend_blend=explicit,
        prior_hierarchy=hierarchy,
    )
    assert evaluator.legend_blend is explicit


def test_hierarchy_weights_remain_soft_not_normalized_into_forced_choice():
    hierarchy = HierarchicalPriorSet(
        domain_prior=_prior(LearningDomain.COMPING, "density", 0.0),
        genre_prior=_prior(LearningDomain.GENRE, "comping_density_mean", 0.0),
        style_prior=_prior(LearningDomain.STYLE, "comping_density_mean", 0.0),
        weights=PriorLayerWeights(domain=.5, genre=.25, style=.25, legend=1.0),
    )
    hierarchy.validate()
    assert hierarchy.weights.domain + hierarchy.weights.genre + hierarchy.weights.style == 1.0
