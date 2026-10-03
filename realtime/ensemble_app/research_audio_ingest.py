"""Autonomous-listener bridge into the canonical Audio Evidence Engine.

The listener owns capture/orchestration only. It does not own detectors,
instrument attribution, form theory, or the persisted musical coordinate.

A concrete streaming bridge for music_intelligence.audio_evidence is injected by
the application boundary. Detector form estimates are converted through
listener_shared_core_adapter before persistence.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Mapping, Protocol

from music_intelligence.corpus.realchord import RealChordSong
from music_intelligence.learning.score_alignment import PerformancePhase

from .listener_shared_core_adapter import coordinate_from_listener_estimate
from .research_checkpoint import default_research_state_root


class CanonicalAudioEvidenceBridge(Protocol):
    def ingest_float32(
        self,
        source_id: str,
        payload: bytes,
        *,
        sample_rate: int,
        timestamp: float | None = None,
    ) -> Mapping[str, object]:
        """Return canonical Audio Evidence / Performance Evidence payload."""


def _jsonable(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return {str(k):_jsonable(v) for k,v in value.items()}
    if isinstance(value, (tuple,list)):
        return [_jsonable(x) for x in value]
    if hasattr(value,"value"):
        return value.value
    return value


class ResearchAudioIngestor:
    def __init__(
        self,
        *,
        evidence_root: Path | None = None,
        bridge: CanonicalAudioEvidenceBridge | None = None,
    ) -> None:
        self.evidence_root=evidence_root or (default_research_state_root()/"evidence")
        self.bridge=bridge
        self._realchord_by_source: dict[str,RealChordSong]={}

    @property
    def canonical_audio_attached(self) -> bool:
        return self.bridge is not None

    def attach_audio_evidence_bridge(self, bridge: CanonicalAudioEvidenceBridge) -> None:
        self.bridge=bridge

    def set_realchord_song(self, source_id: str, song: RealChordSong) -> None:
        if not source_id:
            raise ValueError("source_id is required")
        song.validate()
        self._realchord_by_source[source_id]=song

    def ingest_float32(
        self,
        source_id: str,
        payload: bytes,
        *,
        sample_rate: int,
        timestamp: float | None = None,
        form_estimate: Mapping[str,object] | None = None,
        song_id: str | None = None,
        performance_phase: PerformancePhase = PerformancePhase.UNKNOWN,
    ) -> dict:
        if not source_id:
            raise ValueError("source_id is required")
        if sample_rate < 8000 or sample_rate > 192000:
            raise ValueError("unsupported sample rate")
        if len(payload)%4:
            raise ValueError("Float32 PCM payload length must be divisible by 4")
        if self.bridge is None:
            raise RuntimeError(
                "canonical music_intelligence.audio_evidence streaming bridge is not attached"
            )

        canonical=dict(self.bridge.ingest_float32(
            source_id,
            payload,
            sample_rate=sample_rate,
            timestamp=timestamp,
        ))

        estimate=form_estimate
        if estimate is None:
            candidate=canonical.get("metric_form_position")
            if isinstance(candidate,Mapping):
                estimate=candidate

        realchord=self._realchord_by_source.get(source_id)
        coordinate=coordinate_from_listener_estimate(
            estimate,
            song_id=(realchord.title if realchord is not None else (song_id or source_id)),
            performance_phase=performance_phase,
            realchord_song=realchord,
            confidence=float(canonical.get("form_confidence",.5) or .5),
        )

        row={
            "source_id":source_id,
            "sample_rate":sample_rate,
            "sample_count":len(payload)//4,
            "audio_evidence":_jsonable(canonical),
            "musical_position":_jsonable(coordinate) if coordinate is not None else None,
            "learning_status":(
                "canonical_coordinate_ready" if coordinate is not None
                else "navigation_only"
            ),
            "provenance":[
                "browser_user_authorized_capture",
                "music_intelligence.audio_evidence",
                "listener_shared_core_adapter",
            ],
        }
        self._append_jsonl(source_id,row)
        return row

    def _append_jsonl(self,source_id: str,row: dict) -> None:
        safe="".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in source_id)
        self.evidence_root.mkdir(parents=True,exist_ok=True)
        with (self.evidence_root/f"{safe}.jsonl").open("a",encoding="utf-8") as fh:
            fh.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
