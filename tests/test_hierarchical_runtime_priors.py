import pytest

from music_intelligence.learning import LearningDomain, LearningPriorView
from music_intelligence.reasoning.hierarchical_priors import (
    HierarchicalPriorSet,
    PriorLayerWeights,
    numeric_hierarchy_bias,
)


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


def test_numeric_hierarchy_composes_domain_genre_and_style_softly():
    priors = HierarchicalPriorSet(
        domain_prior=_prior(LearningDomain.COMPING, "density", .5),
        genre_prior=_prior(LearningDomain.GENRE, "comping_density_mean", .5),
        style_prior=_prior(LearningDomain.STYLE, "comping_density_mean", .5),
        weights=PriorLayerWeights(domain=1.0, genre=.5, style=.5, legend=1.0),
    )

    bias = numeric_hierarchy_bias(
        priors,
        observed=.5,
        domain_feature="density",
        genre_feature="comping_density_mean",
        style_feature="comping_density_mean",
        tolerance=.5,
        max_bonus=.1,
    )

    assert bias.total == pytest.approx(.2)
    assert set(bias.components) == {
        "domain:density",
        "genre:comping_density_mean",
        "style:comping_density_mean",
    }


def test_missing_layers_do_not_create_fake_bias():
    priors = HierarchicalPriorSet(
        domain_prior=_prior(LearningDomain.SOLO_PHRASE, "entry_phase", 0.0),
    )
    bias = numeric_hierarchy_bias(
        priors,
        observed=0.0,
        domain_feature="entry_phase",
        genre_feature=None,
        style_feature=None,
        tolerance=1.0,
    )
    assert bias.total > 0
    assert list(bias.components) == ["domain:entry_phase"]
