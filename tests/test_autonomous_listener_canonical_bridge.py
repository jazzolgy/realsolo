from dataclasses import dataclass
from pathlib import Path

import pytest

from realtime.ensemble_app.research_audio_ingest import ResearchAudioIngestor


@dataclass(frozen=True)
class Estimate:
    measure_index: int | None = 7
    beat_in_measure: float | None = 2.5
    section_id: str | None = "A2"
    section_measure_index: int | None = 7
    form_iteration: int | None = 2
    confidence: float = .82


class FakeAudioBridge:
    def ingest_float32(self,source_id,payload,*,sample_rate,timestamp=None):
        return {
            "source_id":source_id,
            "timestamp_s":timestamp,
            "instrument_probabilities":{"piano":.8,"bass":.2},
            "engine":"canonical-test-double",
        }


def test_listener_requires_canonical_audio_bridge(tmp_path: Path):
    ingestor=ResearchAudioIngestor(evidence_root=tmp_path)
    with pytest.raises(RuntimeError,match="canonical Audio Evidence"):
        ingestor.ingest_float32(
            "source",b"\x00"*16,sample_rate=48000,timestamp=1.0
        )


def test_listener_persists_audio_evidence_plus_musical_score_coordinate(tmp_path: Path):
    ingestor=ResearchAudioIngestor(
        evidence_root=tmp_path,
        audio_bridge=FakeAudioBridge(),
    )
    row=ingestor.ingest_float32(
        "source",
        b"\x00"*16,
        sample_rate=48000,
        timestamp=12.5,
        form_estimate=Estimate(),
        song_id="Autumn Leaves",
        score_source_id="realchord:test",
        realchord_id="rc:test",
        form_length_bars=32,
    )
    assert row["audio_evidence"]["engine"]=="canonical-test-double"
    assert row["musical_position"]["song_id"]=="Autumn Leaves"
    assert row["musical_position"]["bar"]==8
    assert row["musical_position"]["form_bar"]==8
    assert row["musical_position"]["chorus_index"]==2
    assert row["learning_status"]=="canonical_coordinate_ready"
