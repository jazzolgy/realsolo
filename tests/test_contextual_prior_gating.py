import pytest

from music_intelligence.reasoning.contextual_prior_gating import (
    PerformanceMode,
    PriorGatingContext,
    derive_prior_gate,
    head_gating_context,
)
from music_intelligence.reasoning.hierarchical_priors import PriorLayerWeights


def test_dense_confident_live_context_reduces_historical_prior_authority():
    base=PriorLayerWeights(domain=1.0,genre=.45,style=.60,legend=1.0)
    result=derive_prior_gate(
        base,
        PriorGatingContext(
            performance_mode=PerformanceMode.IMPROVISATION,
            ensemble_complexity=1.0,
            live_context_confidence=1.0,
        ),
    )
    assert result.weights.domain < base.domain
    assert result.weights.genre < base.genre
    assert result.weights.style < base.style
    assert result.weights.legend < base.legend
    assert result.weights.legend < result.weights.domain


def test_head_mode_strongly_closes_style_and_legend_priors():
    base=PriorLayerWeights()
    gate=head_gating_context(mode="strict",ensemble_complexity=0.0,live_context_confidence=0.0)
    result=derive_prior_gate(base,gate)
    assert result.weights.domain == pytest.approx(.25)
    assert result.weights.genre == pytest.approx(.045)
    assert result.weights.style == pytest.approx(.06)
    assert result.weights.legend == pytest.approx(.08)


def test_loose_head_keeps_more_prior_freedom_than_strict():
    base=PriorLayerWeights()
    strict=derive_prior_gate(base,head_gating_context(mode="strict",ensemble_complexity=0.0,live_context_confidence=0.0))
    loose=derive_prior_gate(base,head_gating_context(mode="loose",ensemble_complexity=0.0,live_context_confidence=0.0))
    assert loose.weights.legend > strict.weights.legend
    assert loose.weights.style > strict.weights.style


def test_gate_never_increases_configured_weights():
    base=PriorLayerWeights(domain=.8,genre=.3,style=.4,legend=.7)
    result=derive_prior_gate(
        base,
        PriorGatingContext(
            ensemble_complexity=.2,
            live_context_confidence=.2,
            structural_constraint=.2,
        ),
    )
    assert result.weights.domain <= base.domain
    assert result.weights.genre <= base.genre
    assert result.weights.style <= base.style
    assert result.weights.legend <= base.legend
