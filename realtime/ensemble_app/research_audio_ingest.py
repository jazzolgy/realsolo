"""Streaming browser PCM -> compact realtime audio evidence.

The browser sends Float32 little-endian mono PCM captured with explicit user
permission. Source media is not persisted here.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import time

from .audio_features import AudioFeatureExtractor
from .research_checkpoint import default_research_state_root
from .instrument_role_detector import (
    AcousticDescriptorFrame,
    BaselineInstrumentRoleDetector,
    TemporalContextCorrector,
)
from music_intelligence.learning.shared_audio_intelligence import (
    DetectorEvidence,
    PerformanceEvidence,
    identity_context_correction,
    musical_moment_from_evidence,
)


class ResearchAudioIngestor:
    def __init__(self, *, evidence_root: Path | None = None) -> None:
        self.evidence_root=evidence_root or (default_research_state_root()/"evidence")
        self._extractors: dict[tuple[str,int],AudioFeatureExtractor]={}
        self._detector=BaselineInstrumentRoleDetector()
        self._context_correctors: dict[str,TemporalContextCorrector]={}

    def ingest_float32(
        self,
        source_id: str,
        payload: bytes,
        *,
        sample_rate: int,
        timestamp: float | None = None,
    ) -> dict:
        if not source_id:
            raise ValueError("source_id is required")
        if sample_rate < 8000 or sample_rate > 192000:
            raise ValueError("unsupported sample rate")
        if len(payload)%4:
            raise ValueError("Float32 PCM payload length must be divisible by 4")
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError('Install audio support with: pip install -e ".[audio]"') from exc
        samples=np.frombuffer(payload,dtype="<f4")
        extractor=self._extractors.setdefault((source_id,sample_rate),AudioFeatureExtractor(sample_rate=sample_rate))
        ts=time.monotonic() if timestamp is None else float(timestamp)
        obs=extractor.process(samples,ts)
        frame=AcousticDescriptorFrame(
            pitch_hz=obs.pitch_hz,
            pitch_confidence=float(obs.pitch_confidence),
            onset=bool(obs.onset),
            onset_strength=float(obs.onset_strength),
            rms=float(obs.rms),
            spectral_centroid_hz=obs.spectral_centroid_hz,
            spectral_flatness=obs.spectral_flatness,
            zero_crossing_rate=obs.zero_crossing_rate,
            low_energy_ratio=obs.low_energy_ratio,
            mid_energy_ratio=obs.mid_energy_ratio,
            high_energy_ratio=obs.high_energy_ratio,
        )
        raw=self._detector.detect(frame)
        corrector=self._context_correctors.setdefault(source_id,TemporalContextCorrector())
        posterior=corrector.correct(raw)
        evidence=PerformanceEvidence(
            source_id=source_id,
            timestamp_s=max(0.0,ts),
            raw=raw,
            posterior=posterior,
            provenance=(
                "browser_user_authorized_capture",
                "realtime_audio_feature_extractor",
                "baseline_instrument_role_detector",
                "temporal_context_corrector",
            ),
        )
        moment=musical_moment_from_evidence(evidence)
        observation_payload=asdict(obs)
        kind=observation_payload.get("kind")
        if hasattr(kind,"value"):
            observation_payload["kind"]=kind.value
        row={
            "source_id":source_id,
            "sample_rate":sample_rate,
            "sample_count":int(samples.size),
            "observation":observation_payload,
            "performance_evidence":asdict(evidence),
            "musical_moment":asdict(moment),
            "provenance":[
                "browser_user_authorized_capture",
                "realtime_audio_feature_extractor",
                "baseline_instrument_role_detector",
                "temporal_context_corrector",
                "shared_audio_intelligence",
            ],
        }
        self._append_jsonl(source_id,row)
        return row

    def _append_jsonl(self,source_id: str,row: dict) -> None:
        safe="".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in source_id)
        self.evidence_root.mkdir(parents=True,exist_ok=True)
        with (self.evidence_root/f"{safe}.jsonl").open("a",encoding="utf-8") as fh:
            fh.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
