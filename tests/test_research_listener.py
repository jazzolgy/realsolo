from realtime.ensemble_app.research_listener import (
    ResearchListenerPolicy,
    ResearchSourceCandidate,
    choose_next_research_source,
    rank_research_candidates,
)


def candidate(source_id: str, **overrides):
    values = dict(
        source_id=source_id,
        provider="youtube",
        title=source_id,
        artist="Bill Evans",
        duration_s=360.0,
        embeddable=True,
        playable=True,
        identity_confidence=0.95,
        source_reliability=0.90,
        audio_suitability=0.85,
        coverage_gap_score=0.50,
        duplicate_penalty=0.0,
        recent_use_penalty=0.0,
    )
    values.update(overrides)
    return ResearchSourceCandidate(**values)


def test_ineligible_sources_are_not_ranked():
    rows = rank_research_candidates(
        [
            candidate("ok"),
            candidate("not-embeddable", embeddable=False),
            candidate("identity-weak", identity_confidence=0.2),
        ]
    )
    assert [x.source_id for x in rows] == ["ok"]


def test_coverage_gap_can_beat_popular_duplicate():
    underrepresented = candidate("underrepresented", coverage_gap_score=0.95)
    duplicate = candidate(
        "duplicate",
        coverage_gap_score=0.55,
        duplicate_penalty=0.90,
    )
    assert choose_next_research_source([duplicate, underrepresented]).source_id == "underrepresented"


def test_equal_scores_are_deterministic():
    rows = rank_research_candidates([candidate("b"), candidate("a")])
    assert [x.source_id for x in rows] == ["a", "b"]


def test_duration_guardrails():
    policy = ResearchListenerPolicy()
    assert not policy.allows(candidate("tiny", duration_s=10.0))
    assert not policy.allows(candidate("huge", duration_s=5 * 60 * 60.0))
