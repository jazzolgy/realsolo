from pathlib import Path

from music_intelligence.audio_evidence import (
    ContextCorrection,
    DetectorEvidence,
    StreamingAudioEvidenceEngine,
)
from realtime.ensemble_app.research_audio_ingest import ResearchAudioIngestor


class Detector:
    def detect_float32(self,source_id,payload,*,sample_rate,timestamp_s):
        return DetectorEvidence(
            instrument_probabilities={"piano":.6},
            role_probabilities={"comping_or_support":.5},
            confidence_fields={"event":.7},
            pitch_hz=440.0,
            onset=True,
            onset_strength=.8,
            rms=.1,
        )


class Corrector:
    def correct(self,source_id,raw,*,timestamp_s):
        return ContextCorrection(
            instrument_probabilities={"piano":.7},
            role_probabilities={"comping_or_support":.6},
            confidence_fields={"event":.75},
            reasons=("test_context",),
        )


def test_streaming_engine_owns_raw_posterior_performance_evidence_contract():
    engine=StreamingAudioEvidenceEngine(Detector(),Corrector())
    evidence=engine.ingest_float32(
        "source",
        b"\x00"*16,
        sample_rate=48000,
        timestamp_s=1.25,
        provenance=("capture",),
    )
    assert evidence.raw.instrument_probabilities["piano"]==.6
    assert evidence.posterior.instrument_probabilities["piano"]==.7
    assert "music_intelligence.audio_evidence:streaming_engine" in evidence.provenance


def test_listener_can_consume_injected_canonical_engine_without_owning_detector(tmp_path: Path):
    engine=StreamingAudioEvidenceEngine(Detector(),Corrector())
    ingestor=ResearchAudioIngestor(
        evidence_root=tmp_path,
        audio_engine=engine,
    )
    row=ingestor.ingest_float32(
        "source",
        b"\x00"*16,
        sample_rate=48000,
        timestamp=2.0,
    )
    pe=row["performance_evidence"]
    assert pe["raw"]["instrument_probabilities"]["piano"]==.6
    assert pe["posterior"]["instrument_probabilities"]["piano"]==.7
    assert row["learning_alignment_status"]=="unaligned"
