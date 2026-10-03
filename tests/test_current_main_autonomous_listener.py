from dataclasses import dataclass

from music_intelligence.audio_evidence import (
    ContextCorrection,
    DetectorEvidence,
    PerformanceEvidence,
    musical_moment_from_evidence,
)
from music_intelligence.learning import PerformancePhase
from realtime.ensemble_app.autonomous_research_session import (
    AutonomousResearchSession,
    ListenerRunState,
)
from realtime.ensemble_app.research_audio_ingest import ResearchAudioIngestor
from realtime.ensemble_app.research_listener import (
    ResearchSourceCandidate,
    ResearchListenerPolicy,
)
from realtime.ensemble_app.youtube_data_api import parse_iso8601_duration_seconds


@dataclass(frozen=True)
class Estimate:
    measure_index: int | None
    beat_in_measure: float | None
    section_id: str | None
    section_measure_index: int | None
    form_iteration: int | None
    confidence: float


def test_listener_source_queue_is_provider_metadata_only():
    session=AutonomousResearchSession(policy=ResearchListenerPolicy())
    good=ResearchSourceCandidate(
        source_id="youtube:good",
        provider="youtube",
        title="Live trio",
        artist="Artist",
        duration_s=300,
        embeddable=True,
        playable=True,
        identity_confidence=.9,
        source_reliability=.8,
        audio_suitability=.9,
        coverage_gap_score=.8,
    )
    blocked=ResearchSourceCandidate(
        source_id="youtube:noembed",
        provider="youtube",
        title="No embed",
        artist="Artist",
        duration_s=300,
        embeddable=False,
        playable=True,
        identity_confidence=.9,
        source_reliability=.8,
        audio_suitability=.9,
        coverage_gap_score=1.0,
    )
    session.replace_candidates((blocked,good))
    assert session.choose_next() == good
    session.mark_playing()
    assert session.run_state is ListenerRunState.PLAYING


def test_listener_position_is_adapted_into_musical_score_coordinate(tmp_path):
    ingestor=ResearchAudioIngestor(evidence_root=tmp_path)
    p=ingestor.set_listener_position(
        "youtube:abc",
        Estimate(7,2.0,"A1",7,1,.84),
        song_id="Autumn Leaves",
        score_source_id="realchord:autumn-leaves",
        realchord_id="autumn-leaves",
        form_length_bars=32,
        performance_phase=PerformancePhase.SOLO,
    )
    assert p.bar == 8
    assert p.form_bar == 8
    assert p.beat == 2.0
    assert p.chorus_index == 1
    assert ingestor.position("youtube:abc") == p
    assert not hasattr(p,"timestamp_s")


def test_audio_evidence_preserves_raw_and_posterior_and_optional_alignment():
    raw=DetectorEvidence(
        instrument_probabilities={"unknown_pitched":.6},
        role_probabilities={"melody_or_solo":.5},
        confidence_fields={"instrument":.6,"role":.5},
        pitch_hz=440.0,
        onset=True,
        onset_strength=.7,
        rms=.1,
    )
    posterior=ContextCorrection(
        instrument_probabilities={"unknown_pitched":.55},
        role_probabilities={"melody_or_solo":.6},
        confidence_fields={"instrument":.55,"role":.6},
        reasons=("temporal_continuity",),
    )
    evidence=PerformanceEvidence(
        source_id="youtube:abc",
        timestamp_s=12.5,
        raw=raw,
        posterior=posterior,
        musical_position=None,
        provenance=("browser_user_authorized_capture",),
    )
    moment=musical_moment_from_evidence(evidence)
    assert evidence.raw.instrument_probabilities["unknown_pitched"] == .6
    assert moment.instrument_probabilities["unknown_pitched"] == .55
    assert moment.musical_position is None


def test_youtube_duration_parser_is_metadata_only_utility():
    assert parse_iso8601_duration_seconds("PT3M30S") == 210.0
