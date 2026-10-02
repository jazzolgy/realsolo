from music_intelligence.legends import (
    ContextualLegendMixture,
    LegendDomain,
    LegendViewWeight,
    VocabularyMemoryItem,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.legends.parker import PARKER_PROFILE_VIEW
from music_intelligence.legends.parker.vocabulary import ParkerVocabularyIndex
from players.sax.candidates import (
    SaxLegendCandidateContext,
    collect_legend_candidate_material,
)
from players.sax.legend_context import SaxLegendContext
from players.sax.policy import choose_legend_memory_intention


def _memory():
    return VocabularyMemoryItem(
        vocabulary_id="CP-FRAG-012",
        source_id="cp-test",
        harmony_context="Dm7 G7 Cmaj7",
        harmonic_function="ii_v_i",
        local_key="C",
        phrase_position="middle",
        domains=frozenset({LegendDomain.LINEAR_CONNECTION}),
        context_tags=frozenset({"passing"}),
        candidate_uses=frozenset({
            VocabularyUseType.FRAGMENT_RECALL,
            VocabularyUseType.HYBRID_COMPOSITION,
        }),
        recent_usage_count=2,
        confidence=.9,
    )


def test_sax_forwards_latest_vocabulary_query_contract():
    idx = ParkerVocabularyIndex((_memory(),))
    sax = SaxLegendContext(PARKER_PROFILE_VIEW, idx)
    results = sax.vocabulary(
        domain=LegendDomain.LINEAR_CONNECTION,
        harmony_context="Dm7 G7 Cmaj7",
        harmonic_function="ii_v_i",
        local_key="C",
        phrase_position="middle",
        context_tags=frozenset({"passing"}),
        allowed_uses=frozenset({VocabularyUseType.HYBRID_COMPOSITION}),
    )
    assert [x.vocabulary_id for x in results] == ["CP-FRAG-012"]


def test_sax_candidate_material_contains_prior_and_memory_without_future_notes():
    idx = ParkerVocabularyIndex((_memory(),))
    mixture = ContextualLegendMixture((LegendViewWeight(PARKER_PROFILE_VIEW, 1.0),))
    sax = SaxLegendContext(PARKER_PROFILE_VIEW, idx, mixture=mixture)
    ctx = SaxLegendCandidateContext(
        domain=LegendDomain.LINEAR_CONNECTION,
        harmony_context="Dm7 G7 Cmaj7",
        harmonic_function="ii_v_i",
        local_key="C",
        phrase_position="middle",
        active_tags=("passing",),
        allowed_uses=frozenset({VocabularyUseType.HYBRID_COMPOSITION}),
    )
    materials = collect_legend_candidate_material(sax, ctx)
    assert any(x.source_family == "legend_prior" for x in materials)
    assert any(
        x.source_family == "legend_vocabulary"
        and x.use_type is VocabularyUseType.HYBRID_COMPOSITION
        for x in materials
    )
    assert all(not hasattr(x, "exact_future_notes") for x in materials)


def test_policy_selects_soft_memory_intention_not_phrase():
    idx = ParkerVocabularyIndex((_memory(),))
    sax = SaxLegendContext(PARKER_PROFILE_VIEW, idx)
    ctx = SaxLegendCandidateContext(
        domain=LegendDomain.LINEAR_CONNECTION,
        harmony_context="Dm7 G7 Cmaj7",
        harmonic_function="ii_v_i",
        local_key="C",
        phrase_position="middle",
        active_tags=("passing",),
        allowed_uses=frozenset({VocabularyUseType.HYBRID_COMPOSITION}),
    )
    decision = choose_legend_memory_intention(sax, ctx)
    assert decision.materials
    if decision.intention is not None:
        assert decision.intention.use_type is VocabularyUseType.HYBRID_COMPOSITION
        assert not hasattr(decision.intention, "exact_future_notes")
