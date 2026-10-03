"""Browser-authorized PCM -> canonical Shared Audio Evidence.

The listener owns capture, timestamps, and optional alignment state. Detector
implementations are adapters; StreamingAudioEvidenceEngine owns construction of
raw/posterior PerformanceEvidence.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import time

from music_intelligence.audio_evidence import (
    StreamingAudioEvidenceEngine,
    musical_moment_from_evidence,
)
from music_intelligence.learning import (
    MusicalScoreCoordinate,
    PerformancePhase,
    coordinate_from_listener_estimate,
)

from .learned_instrument_adapter import LearnedInstrumentBackend
from .listener_audio_evidence_backend import ListenerAudioEvidenceBackend
from .research_checkpoint import default_research_state_root


class ResearchAudioIngestor:
    def __init__(
        self,
        *,
        evidence_root: Path | None = None,
        learned_instrument_backend: LearnedInstrumentBackend | None = None,
        audio_engine: StreamingAudioEvidenceEngine | None = None,
        audio_backend: ListenerAudioEvidenceBackend | None = None,
    ) -> None:
        self.evidence_root=evidence_root or (default_research_state_root()/"evidence")
        if audio_engine is not None and audio_backend is not None:
            raise ValueError("pass audio_engine or audio_backend, not both")
        if audio_engine is not None:
            self._engine=audio_engine
            self._backend=None
        else:
            backend=audio_backend or ListenerAudioEvidenceBackend(
                learned_instrument_backend=learned_instrument_backend
            )
            self._backend=backend
            self._engine=StreamingAudioEvidenceEngine(
                detector=backend,
                context_corrector=backend,
            )
        self._source_origins: dict[str,float]={}
        self._musical_positions: dict[str,MusicalScoreCoordinate]={}

    @property
    def audio_engine(self) -> StreamingAudioEvidenceEngine:
        return self._engine

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
        if timestamp is None:
            now=time.monotonic()
            origin=self._source_origins.setdefault(source_id,now)
            ts=max(0.0,now-origin)
        else:
            ts=max(0.0,float(timestamp))

        position=musical_position or self._musical_positions.get(source_id)
        evidence=self._engine.ingest_float32(
            source_id,
            payload,
            sample_rate=sample_rate,
            timestamp_s=ts,
            musical_position=position,
            provenance=("browser_user_authorized_capture",),
        )

        moment_kwargs=(
            self._backend.musical_moment_kwargs(source_id)
            if self._backend is not None else {}
        )
        moment=musical_moment_from_evidence(evidence,**moment_kwargs)
        observation_payload=(
            self._backend.observation_payload(source_id)
            if self._backend is not None else {}
        )

        row={
            "source_id":source_id,
            "sample_rate":sample_rate,
            "sample_count":len(payload)//4,
            "observation":observation_payload,
            "performance_evidence":asdict(evidence),
            "musical_moment":asdict(moment),
            "learning_alignment_status":(
                position.alignment_status.value if position is not None else "unaligned"
            ),
            "provenance":[
                "browser_user_authorized_capture",
                "music_intelligence.audio_evidence:streaming_engine",
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
