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
        confidence_fields={
            "pitch":float(obs.pitch_confidence),
            "onset":min(1.0,max(0.0,float(obs.onset_strength))),
            "event":max(float(obs.pitch_confidence), min(1.0,max(0.0,float(obs.onset_strength)))),
        }
        raw=DetectorEvidence(
            instrument_probabilities={},
            role_probabilities={},
            confidence_fields=confidence_fields,
            pitch_hz=obs.pitch_hz,
            onset=bool(obs.onset),
            onset_strength=float(obs.onset_strength),
            rms=float(obs.rms),
        )
        evidence=PerformanceEvidence(
            source_id=source_id,
            timestamp_s=max(0.0,ts),
            raw=raw,
            posterior=identity_context_correction(raw),
            provenance=(
                "browser_user_authorized_capture",
                "realtime_audio_feature_extractor",
            ),
        )
        moment=musical_moment_from_evidence(evidence)
        row={
            "source_id":source_id,
            "sample_rate":sample_rate,
            "sample_count":int(samples.size),
            "observation":asdict(obs),
            "performance_evidence":asdict(evidence),
            "musical_moment":asdict(moment),
            "provenance":[
                "browser_user_authorized_capture",
                "realtime_audio_feature_extractor",
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
