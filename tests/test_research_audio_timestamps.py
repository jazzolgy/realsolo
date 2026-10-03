import json
import numpy as np

from realtime.ensemble_app.research_audio_ingest import ResearchAudioIngestor


def test_explicit_media_time_is_used_as_source_timestamp(tmp_path):
    ingestor=ResearchAudioIngestor(evidence_root=tmp_path)
    payload=np.zeros(4096,dtype="<f4").tobytes()
    row=ingestor.ingest_float32(
        "youtube:test",
        payload,
        sample_rate=48000,
        timestamp=12.75,
    )
    assert row["performance_evidence"]["timestamp_s"] == 12.75
    assert row["musical_moment"]["timestamp_s"] == 12.75


def test_fallback_timestamp_starts_near_zero_for_each_source(tmp_path):
    ingestor=ResearchAudioIngestor(evidence_root=tmp_path)
    payload=np.zeros(4096,dtype="<f4").tobytes()
    first=ingestor.ingest_float32("youtube:a",payload,sample_rate=48000)
    second=ingestor.ingest_float32("youtube:b",payload,sample_rate=48000)
    assert 0.0 <= first["performance_evidence"]["timestamp_s"] < 1.0
    assert 0.0 <= second["performance_evidence"]["timestamp_s"] < 1.0
