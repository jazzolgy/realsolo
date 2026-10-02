from music_intelligence.legends import (
    ContextualLegendMixture,
    LegendDomain,
    LegendViewWeight,
    VocabularyMemoryItem,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.legends.parker import (
    PARKER_ONLINE_PROFILE,
    PARKER_PROFILE_VIEW,
    PARKER_RUNTIME_BLEND,
    PARKER_VOCABULARY_INDEX,
    build_statistics,
)
from music_intelligence.legends.parker.vocabulary import ParkerVocabularyIndex
from music_intelligence.reasoning.legend_style_core import CandidateEvent, MusicalContextVector
from music_intelligence.reasoning.online_improviser import OnlineMusicalEvaluator


def test_parker_v2_profile_view_is_domain_queryable_across_evidence_layers():
    items = PARKER_PROFILE_VIEW.tendencies(
        domain=LegendDomain.LINEAR_CONNECTION,
        active_tags=("passing", "neighbor", "close_approach", "after_wide_leap"),
    )
    features = {x.feature for x in items}
    assert {"passing", "neighbor", "close_approach"} <= features
    assert "contrary_recovery" in features


def test_vocabulary_use_types_include_jazz_memory_and_hybrid_composition():
    assert VocabularyUseType.LITERAL_QUOTE.value == "literal_quote"
    assert VocabularyUseType.HYBRID_COMPOSITION.value == "hybrid_composition"
    q = VocabularyQuery("charlie_parker")
    assert VocabularyUseType.LITERAL_QUOTE in q.allowed_uses
    assert PARKER_VOCABULARY_INDEX.query(q) == ()


def test_vocabulary_query_filters_candidate_family_and_context():
    literal = VocabularyMemoryItem(
        vocabulary_id="CP-LICK-1",
        source_id="source-a",
        harmonic_function="dominant",
        phrase_position="late",
        domains=frozenset({LegendDomain.LINEAR_CONNECTION}),
        context_tags=frozenset({"answer"}),
        candidate_uses=frozenset({
            VocabularyUseType.LITERAL_QUOTE,
            VocabularyUseType.TRANSPOSED_LICK,
        }),
        confidence=.9,
    )
    hybrid = VocabularyMemoryItem(
        vocabulary_id="CP-FRAG-2",
        source_id="source-b",
        harmonic_function="dominant",
        phrase_position="late",
        domains=frozenset({LegendDomain.MOTIF_DEVELOPMENT}),
        context_tags=frozenset({"answer"}),
        candidate_uses=frozenset({VocabularyUseType.HYBRID_COMPOSITION}),
        confidence=.8,
    )
    index = ParkerVocabularyIndex((literal, hybrid))
    out = index.query(VocabularyQuery(
        "charlie_parker",
        domain=LegendDomain.LINEAR_CONNECTION,
        harmonic_function="dominant",
        phrase_position="late",
        context_tags=frozenset({"answer"}),
        allowed_uses=frozenset({VocabularyUseType.LITERAL_QUOTE}),
    ))
    assert tuple(x.vocabulary_id for x in out) == ("CP-LICK-1",)


def test_recent_usage_applies_repetition_pressure():
    fresh = VocabularyMemoryItem(
        vocabulary_id="fresh",
        source_id="s",
        candidate_uses=frozenset({VocabularyUseType.FRAGMENT_RECALL}),
        confidence=.8,
    )
    repeated = VocabularyMemoryItem(
        vocabulary_id="repeated",
        source_id="s",
        candidate_uses=frozenset({VocabularyUseType.FRAGMENT_RECALL}),
        confidence=.9,
        recent_usage_count=4,
    )
    out = ParkerVocabularyIndex((repeated, fresh)).query(
        VocabularyQuery("charlie_parker", allowed_uses=frozenset({VocabularyUseType.FRAGMENT_RECALL}))
    )
    assert out[0].vocabulary_id == "fresh"


def test_parker_conditional_stats_migrated_without_changing_regression():
    s = build_statistics()
    assert s.corpus_licks == 131
    assert 0.60 < s.global_motion.step_share < 0.63


def test_runtime_blend_remains_immediate_candidate_prior():
    ev = OnlineMusicalEvaluator(PARKER_RUNTIME_BLEND)
    ctx = MusicalContextVector(phrase_maturity=.8, ensemble_activity=.75)
    rest = ev.evaluate(CandidateEvent(None, 1.0, tags=frozenset({"ensemble_space"})), ctx)
    assert rest.total > 0
    assert PARKER_ONLINE_PROFILE.instrument_family == "alto_saxophone"


def test_contextual_legend_mixture_is_domain_specific():
    mix = ContextualLegendMixture((LegendViewWeight(PARKER_PROFILE_VIEW, 1.0),))
    bias = mix.feature_bias(
        domain=LegendDomain.INTERVAL_LEAP_GRAMMAR,
        feature="contrary_recovery",
        active_tags=("after_wide_leap",),
    )
    assert bias > 0
    assert mix.feature_bias(
        domain=LegendDomain.HEAD_INTERPRETATION,
        feature="contrary_recovery",
        active_tags=("after_wide_leap",),
    ) == 0
