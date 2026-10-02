from music_intelligence.legends import LegendDomain, VocabularyQuery, VocabularyUseType
from music_intelligence.legends.parker import (
    PARKER_ONLINE_PROFILE,
    PARKER_PROFILE_VIEW,
    PARKER_RUNTIME_BLEND,
    PARKER_VOCABULARY_INDEX,
    build_statistics,
)
from music_intelligence.reasoning.legend_style_core import CandidateEvent, MusicalContextVector
from music_intelligence.reasoning.online_improviser import OnlineMusicalEvaluator


def test_parker_v2_profile_view_is_domain_queryable():
    items = PARKER_PROFILE_VIEW.tendencies(
        domain=LegendDomain.LINEAR_CONNECTION,
        active_tags=("passing", "neighbor", "close_approach"),
    )
    assert items
    assert {x.feature for x in items} <= {"passing", "neighbor", "close_approach"}


def test_vocabulary_use_types_include_jazz_memory_and_hybrid_composition():
    assert VocabularyUseType.LITERAL_QUOTE.value == "literal_quote"
    assert VocabularyUseType.HYBRID_COMPOSITION.value == "hybrid_composition"
    q = VocabularyQuery("charlie_parker")
    assert VocabularyUseType.LITERAL_QUOTE in q.allowed_uses
    assert PARKER_VOCABULARY_INDEX.query(q) == ()


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
