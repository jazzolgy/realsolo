from pathlib import Path

from realtime.ensemble_app.autonomous_research_session import AutonomousResearchSession
from realtime.ensemble_app.research_checkpoint import ResearchCheckpoint
from realtime.ensemble_app.youtube_data_api import (
    parse_iso8601_duration_seconds,
)
from realtime.ensemble_app.research_listener import ResearchSourceCandidate


def _candidate(source_id: str):
    return ResearchSourceCandidate(
        source_id=source_id,
        provider="youtube",
        title=source_id,
        artist="open-discovery",
        duration_s=300,
        embeddable=True,
        playable=True,
        identity_confidence=.9,
        source_reliability=.8,
        audio_suitability=.8,
        coverage_gap_score=.7,
    )


def test_youtube_duration_parser():
    assert parse_iso8601_duration_seconds("PT3M30S") == 210
    assert parse_iso8601_duration_seconds("PT1H2M3S") == 3723
    assert parse_iso8601_duration_seconds("P1DT1H") == 90000
    assert parse_iso8601_duration_seconds(None) is None


def test_checkpoint_roundtrip(tmp_path: Path):
    session=AutonomousResearchSession()
    session.replace_candidates((_candidate("youtube:a"),_candidate("youtube:b")))
    session.choose_next()
    session.mark_playing()
    session.mark_complete()
    checkpoint=ResearchCheckpoint.from_session(
        session,
        last_query="jazz live performance",
        last_artist="",
    )
    path=tmp_path/"checkpoint.json"
    checkpoint.save(path)

    restored=ResearchCheckpoint.load(path)
    other=AutonomousResearchSession()
    restored.restore_session(other)
    assert "youtube:a" in other.completed_source_ids
    assert restored.last_query=="jazz live performance"


def test_checkpoint_restore_does_not_invent_queue(tmp_path: Path):
    checkpoint=ResearchCheckpoint(
        completed_source_ids=["youtube:done"],
        run_state="paused",
    )
    path=tmp_path/"checkpoint.json"
    checkpoint.save(path)
    restored=ResearchCheckpoint.load(path)
    session=AutonomousResearchSession()
    restored.restore_session(session)
    assert session.queue == []
    assert session.completed_source_ids == {"youtube:done"}
