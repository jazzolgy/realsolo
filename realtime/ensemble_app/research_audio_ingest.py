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
from .beat_tracker import AdaptiveBeatTracker
from .phrase_tracker import PhraseTracker
from .research_checkpoint import default_research_state_root
from .instrument_role_detector import (
    AcousticDescriptorFrame,
    TemporalContextCorrector,
)
from .learned_instrument_adapter import (
    HybridInstrumentRoleDetector,
    LearnedInstrumentBackend,
    LearnedInstrumentRoleAdapter,
)
from .musical_context_corrector import MusicalContextCorrector, MusicalContextFrame
from music_intelligence.learning.form_position import FormMap, MetricFormPosition
from music_intelligence.form_intelligence import FormObservation, SharedFormIntelligence
from music_intelligence.learning.shared_audio_intelligence import (
    DetectorEvidence,
    PerformanceEvidence,
    musical_moment_from_evidence,
)


class ResearchAudioIngestor:
    def __init__(
        self,
        *,
        evidence_root: Path | None = None,
        learned_instrument_backend: LearnedInstrumentBackend | None = None,
    ) -> None:
        self.evidence_root=evidence_root or (default_research_state_root()/"evidence")
        self._extractors: dict[tuple[str,int],AudioFeatureExtractor]={}
        self._detector=HybridInstrumentRoleDetector(
            learned=(LearnedInstrumentRoleAdapter(learned_instrument_backend) if learned_instrument_backend is not None else None)
        )
        self._context_correctors: dict[str,TemporalContextCorrector]={}
        self._musical_context_correctors: dict[str,MusicalContextCorrector]={}
        self._beat_trackers: dict[str,AdaptiveBeatTracker]={}
        self._phrase_trackers: dict[str,PhraseTracker]={}
        self._source_origins: dict[str,float]={}
        self._form_intelligence: dict[str,SharedFormIntelligence]={}

    def ingest_float32(
        self,
        source_id: str,
        payload: bytes,
        *,
        sample_rate: int,
        timestamp: float | None = None,
        metric_form_position: MetricFormPosition | None = None,
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
        if timestamp is None:
            now=time.monotonic()
            origin=self._source_origins.setdefault(source_id,now)
            ts=max(0.0,now-origin)
        else:
            ts=max(0.0,float(timestamp))
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
        raw=self._detector.detect(samples,sample_rate=sample_rate,frame=frame)
        beat_tracker=self._beat_trackers.setdefault(source_id,AdaptiveBeatTracker())
        beat=beat_tracker.update(obs)
        phrase_tracker=self._phrase_trackers.setdefault(source_id,PhraseTracker())
        phrase=phrase_tracker.update(obs,beat)
        temporal=self._context_correctors.setdefault(source_id,TemporalContextCorrector()).correct(raw)
        musical_context=MusicalContextFrame(
            beat=beat,
            phrase=phrase,
            pitch_hz=obs.pitch_hz,
            onset=bool(obs.onset),
        )
        posterior=self._musical_context_correctors.setdefault(
            source_id,MusicalContextCorrector()
        ).correct(raw,temporal,musical_context)
        if metric_form_position is None:
            form_engine=self._form_intelligence.setdefault(
                source_id,
                SharedFormIntelligence(song_id=source_id),
            )
            form_state=form_engine.update(FormObservation(
                source_time_s=max(0.0,ts),
                absolute_beat=None,
                beat_confidence=float(beat.confidence),
                provenance=(
                    "research_listener",
                    "awaiting_shared_beat_meter_alignment",
                ),
            ))
            metric_form_position=form_state.position
        metric_form_position.validate()
        evidence=PerformanceEvidence(
            source_id=source_id,
            timestamp_s=max(0.0,ts),
            raw=raw,
            posterior=posterior,
            provenance=(
                "browser_user_authorized_capture",
                "realtime_audio_feature_extractor",
                "hybrid_instrument_role_detector",
                "temporal_context_corrector",
                "beat_phrase_context_corrector",
                "canonical_metric_form_address_pending",
            ),
            metric_form_position=metric_form_position,
        )
        moment=musical_moment_from_evidence(
            evidence,
            tempo_bpm=beat.tempo_bpm if beat.confidence >= .35 else None,
            beat_position=beat.phase if beat.confidence >= .35 else None,
            register_center=(obs.note if obs.pitch_confidence >= .45 else None),
            metric_form_position=metric_form_position,
        )
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
                "hybrid_instrument_role_detector",
                "temporal_context_corrector",
                "shared_audio_intelligence",
            ],
        }
        self._append_jsonl(source_id,row)
        return row

    def set_expected_form(
        self,
        source_id: str,
        form_map: FormMap,
        *,
        form_source_id: str,
        song_id: str | None = None,
    ) -> None:
        if not source_id:
            raise ValueError("source_id is required")
        engine=self._form_intelligence.get(source_id)
        if engine is None:
            engine=SharedFormIntelligence(song_id=song_id or source_id)
            self._form_intelligence[source_id]=engine
        engine.set_expected_form(form_map,source_id=form_source_id)

    def form_state(self,source_id: str):
        engine=self._form_intelligence.get(source_id)
        return engine.state if engine is not None else None

    def _append_jsonl(self,source_id: str,row: dict) -> None:
        safe="".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in source_id)
        self.evidence_root.mkdir(parents=True,exist_ok=True)
        with (self.evidence_root/f"{safe}.jsonl").open("a",encoding="utf-8") as fh:
            fh.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
