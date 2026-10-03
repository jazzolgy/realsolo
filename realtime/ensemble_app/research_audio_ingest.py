"""Browser-authorized PCM -> canonical Shared Audio Evidence.

The listener owns source playback/capture and transient detector state. It does
not own a second form coordinate system. A detector form estimate may be
adapted through set_listener_position; persisted evidence stores only
MusicalScoreCoordinate when such an alignment is actually available.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import time

from music_intelligence.audio_evidence import (
    PerformanceEvidence,
    musical_moment_from_evidence,
)
from music_intelligence.learning import (
    MusicalScoreCoordinate,
    PerformancePhase,
    coordinate_from_listener_estimate,
)

from .audio_features import AudioFeatureExtractor
from .beat_tracker import AdaptiveBeatTracker
from .phrase_tracker import PhraseTracker
from .research_checkpoint import default_research_state_root
from .instrument_role_detector import AcousticDescriptorFrame, TemporalContextCorrector
from .learned_instrument_adapter import (
    HybridInstrumentRoleDetector,
    LearnedInstrumentBackend,
    LearnedInstrumentRoleAdapter,
)
from .musical_context_corrector import MusicalContextCorrector, MusicalContextFrame


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
            learned=(
                LearnedInstrumentRoleAdapter(learned_instrument_backend)
                if learned_instrument_backend is not None else None
            )
        )
        self._context_correctors: dict[str,TemporalContextCorrector]={}
        self._musical_context_correctors: dict[str,MusicalContextCorrector]={}
        self._beat_trackers: dict[str,AdaptiveBeatTracker]={}
        self._phrase_trackers: dict[str,PhraseTracker]={}
        self._source_origins: dict[str,float]={}
        self._musical_positions: dict[str,MusicalScoreCoordinate]={}

    def set_musical_position(
        self,
        source_id: str,
        position: MusicalScoreCoordinate | None,
    ) -> None:
        if not source_id:
            raise ValueError("source_id is required")
        if position is None:
            self._musical_positions.pop(source_id,None)
            return
        position.validate()
        self._musical_positions[source_id]=position

    def set_listener_position(
        self,
        source_id: str,
        estimate,
        *,
        song_id: str,
        score_source_id: str="",
        realchord_id: str="",
        form_length_bars: int | None=None,
        performance_phase: PerformancePhase=PerformancePhase.UNKNOWN,
        provenance: tuple[str,...]=(),
    ) -> MusicalScoreCoordinate:
        """Adapt a transient Listener estimate to the one canonical coordinate."""
        position=coordinate_from_listener_estimate(
            estimate,
            song_id=song_id,
            score_source_id=score_source_id,
            realchord_id=realchord_id,
            form_length_bars=form_length_bars,
            performance_phase=performance_phase,
            provenance=provenance+("autonomous_research_listener",),
        )
        self.set_musical_position(source_id,position)
        return position

    def ingest_float32(
        self,
        source_id: str,
        payload: bytes,
        *,
        sample_rate: int,
        timestamp: float | None=None,
        musical_position: MusicalScoreCoordinate | None=None,
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
        extractor=self._extractors.setdefault(
            (source_id,sample_rate),AudioFeatureExtractor(sample_rate=sample_rate)
        )
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
        beat=self._beat_trackers.setdefault(source_id,AdaptiveBeatTracker()).update(obs)
        phrase=self._phrase_trackers.setdefault(source_id,PhraseTracker()).update(obs,beat)
        temporal=self._context_correctors.setdefault(
            source_id,TemporalContextCorrector()
        ).correct(raw)
        posterior=self._musical_context_correctors.setdefault(
            source_id,MusicalContextCorrector()
        ).correct(
            raw,
            temporal,
            MusicalContextFrame(
                beat=beat,
                phrase=phrase,
                pitch_hz=obs.pitch_hz,
                onset=bool(obs.onset),
            ),
        )

        position=musical_position or self._musical_positions.get(source_id)
        if position is not None:
            position.validate()

        evidence=PerformanceEvidence(
            source_id=source_id,
            timestamp_s=ts,
            raw=raw,
            posterior=posterior,
            musical_position=position,
            provenance=(
                "browser_user_authorized_capture",
                "realtime_audio_feature_extractor",
                "hybrid_instrument_role_detector",
                "temporal_context_corrector",
                "beat_phrase_context_corrector",
                (
                    "canonical_musical_position_attached"
                    if position is not None
                    else "musical_position_unresolved"
                ),
            ),
        )
        evidence.validate()
        moment=musical_moment_from_evidence(
            evidence,
            tempo_bpm=beat.tempo_bpm if beat.confidence >= .35 else None,
            beat_position=beat.phase if beat.confidence >= .35 else None,
            register_center=(obs.note if obs.pitch_confidence >= .45 else None),
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
            "learning_alignment_status":(
                position.alignment_status.value if position is not None else "unaligned"
            ),
            "provenance":[
                "browser_user_authorized_capture",
                "canonical_audio_evidence",
                "musical_score_coordinate" if position is not None else "awaiting_alignment",
            ],
        }
        self._append_jsonl(source_id,row)
        return row

    def position(self,source_id: str) -> MusicalScoreCoordinate | None:
        return self._musical_positions.get(source_id)

    def _append_jsonl(self,source_id: str,row: dict) -> None:
        safe="".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in source_id)
        self.evidence_root.mkdir(parents=True,exist_ok=True)
        with (self.evidence_root/f"{safe}.jsonl").open("a",encoding="utf-8") as fh:
            fh.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
