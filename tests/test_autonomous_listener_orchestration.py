from realtime.ensemble_app.autonomous_research_session import (
    AutonomousResearchSession,
    ListenerRunState,
)
from realtime.ensemble_app.research_listener import ResearchSourceCandidate
from realtime.ensemble_app.youtube_research_provider import (
    YouTubeSearchResult,
    youtube_embed_url,
)


def candidate(source_id,gap):
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


def test_listener_session_remains_orchestration_only_and_resumable():
    session=AutonomousResearchSession()
    session.replace_candidates((candidate("a",.9),candidate("b",.7)))
    assert session.choose_next().source_id=="a"
    session.mark_playing()
    session.fail_current()
    assert session.run_state is ListenerRunState.FAILED
    session.resume()
    assert session.choose_next().source_id=="b"


def test_youtube_source_projects_to_official_embed_reference():
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
    item=result.to_candidate(artist="Bill Evans",coverage_gap_score=.7)
    assert item.provider=="youtube"
    assert item.metadata["video_id"]=="abc123"
    assert youtube_embed_url("abc123").startswith("https://www.youtube.com/embed/")
