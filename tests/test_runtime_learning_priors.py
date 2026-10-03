import pytest

from music_intelligence.learning import LearningDomain, LearningPriorView
from music_intelligence.reasoning.learning_prior_runtime import (
    categorical_prior_bias,
    circular_phase_bias,
    numeric_target_bias,
    strongest_category,
)


def _prior():
    return LearningPriorView(
        domain=LearningDomain.RHYTHM_GROOVE,
        numeric_features={"density": .5, "entry_phase": 3.9},
        categorical_counts={"best_groove_grammar": {"swing": 1, "bossa": 1}},
        feedback_bias={},
        observations=2,
        numeric_weights={"density": 1.0, "entry_phase": 1.0},
        categorical_weights={"best_groove_grammar": {"swing": 1.5, "bossa": .5}},
        weighted_observations=2.0,
    )


def test_numeric_prior_is_soft_and_bounded():
    near = numeric_target_bias(_prior(), "density", .52, tolerance=.5)
    far = numeric_target_bias(_prior(), "density", 1.0, tolerance=.5)
    assert near.score_delta > 0
    assert far.score_delta < near.score_delta
    assert abs(near.score_delta) <= .08


def test_circular_phase_wraps_across_bar_boundary():
    near = circular_phase_bias(_prior(), "entry_phase", .05, cycle=4.0, tolerance=.5)
    assert near.score_delta > 0


def test_categorical_prior_uses_weighted_category_distribution():
    bias = categorical_prior_bias(_prior(), "best_groove_grammar", "swing")
    assert bias.score_delta == pytest.approx(.08 * .75)
    assert strongest_category(_prior(), "best_groove_grammar") == ("swing", .75)
