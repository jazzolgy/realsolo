from realtime.ensemble_app.autonomous_research_session import (
    AutonomousResearchSession,
    ListenerRunState,
)
from realtime.ensemble_app.research_listener import ResearchSourceCandidate
from realtime.ensemble_app.research_priority import (
    ResearchGap,
    ResearchPriorityOverride,
    prioritize_research_gaps,
)
from realtime.ensemble_app.youtube_research_provider import (
    YouTubeSearchResult,
    youtube_embed_url,
)


def _candidate(source_id, gap):
    return ResearchSourceCandidate(
        source_id=source_id,
        provider="youtube",
        title=source_id,
        artist="artist",
        duration_s=300,
        embeddable=True,
        playable=True,
        identity_confidence=.9,
        source_reliability=.8,
        audio_suitability=.8,
        coverage_gap_score=gap,
    )


def test_autonomous_session_skips_failed_source_and_continues():
    s=AutonomousResearchSession()
    s.replace_candidates((_candidate("a",.9),_candidate("b",.7)))
    assert s.choose_next().source_id=="a"
    s.mark_playing()
    s.fail_current()
    assert s.run_state is ListenerRunState.FAILED
    s.resume()
    assert s.choose_next().source_id=="b"


def test_priority_override_steers_without_creating_fixed_curriculum():
    gaps=(
        ResearchGap("musician","Bill Evans",.8),
        ResearchGap("musician","John Coltrane",.6),
    )
    normal=prioritize_research_gaps(gaps)
    assert normal[0].target=="Bill Evans"

    override=ResearchPriorityOverride(
        musician_weights={"John Coltrane":2.0,"Bill Evans":.5},
        note="temporary user direction",
    )
    steered=prioritize_research_gaps(gaps,override=override)
    assert steered[0].target=="John Coltrane"


def test_youtube_provider_result_projects_to_research_candidate():
    result=YouTubeSearchResult(
        video_id="abc123",
        title="Live performance",
        channel_title="Archive",
        duration_s=600,
        embeddable=True,
        playable=True,
        identity_confidence=.9,
        source_reliability=.8,
        audio_suitability=.75,
    )
    c=result.to_candidate(artist="Bill Evans",coverage_gap_score=.7)
    assert c.provider=="youtube"
    assert c.metadata["video_id"]=="abc123"
    assert youtube_embed_url("abc123").startswith("https://www.youtube.com/embed/")
