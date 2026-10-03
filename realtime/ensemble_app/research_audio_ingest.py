"""Autonomous-listener capture bridge to canonical Shared Core.

The listener owns browser capture and orchestration only. Audio interpretation is
injected through a canonical Audio Evidence bridge. Transient form estimates are
converted with music_intelligence.learning.listener_position_adapter before any
learning/comparison persistence.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Mapping, Protocol

from music_intelligence.learning.listener_position_adapter import (
    ListenerFormEstimate,
    coordinate_from_listener_estimate,
)
from music_intelligence.learning.score_alignment import PerformancePhase

from .research_checkpoint import default_research_state_root


class StreamingAudioEvidenceBridge(Protocol):
    """Streaming adapter implemented by the canonical Audio Evidence workstream."""

    def ingest_float32(
        self,
        source_id: str,
        payload: bytes,
        *,
        sample_rate: int,
        timestamp: float | None = None,
    ) -> Mapping[str, object]:
        ...


def _jsonable(value):
    if is_dataclass(value):
        return {k:_jsonable(v) for k,v in asdict(value).items()}
    if isinstance(value,Mapping):
        return {str(k):_jsonable(v) for k,v in value.items()}
    if isinstance(value,(tuple,list,set,frozenset)):
        return [_jsonable(v) for v in value]
    if hasattr(value,"value"):
        return value.value
    return value


class ResearchAudioIngestor:
    """Persist canonical evidence plus canonical musical location only."""

    def __init__(
        self,
        *,
        evidence_root: Path | None = None,
        audio_bridge: StreamingAudioEvidenceBridge | None = None,
    ) -> None:
        self.evidence_root=evidence_root or (default_research_state_root()/"evidence")
        self.audio_bridge=audio_bridge

    @property
    def canonical_audio_attached(self) -> bool:
        return self.audio_bridge is not None

    def attach_audio_bridge(self, bridge: StreamingAudioEvidenceBridge) -> None:
        self.audio_bridge=bridge

    def ingest_float32(
        self,
        source_id: str,
        payload: bytes,
        *,
        sample_rate: int,
        timestamp: float | None = None,
        form_estimate: ListenerFormEstimate | None = None,
        song_id: str | None = None,
        score_source_id: str = "",
        realchord_id: str = "",
        form_length_bars: int | None = None,
        performance_phase: PerformancePhase = PerformancePhase.UNKNOWN,
    ) -> dict:
        if not source_id:
            raise ValueError("source_id is required")
        if sample_rate < 8000 or sample_rate > 192000:
            raise ValueError("unsupported sample rate")
        if len(payload)%4:
            raise ValueError("Float32 PCM payload must contain complete samples")
        if self.audio_bridge is None:
            raise RuntimeError(
                "canonical Audio Evidence streaming bridge is not attached; "
                "listener-local detector fallback is intentionally disabled"
            )

        evidence=dict(self.audio_bridge.ingest_float32(
            source_id,payload,sample_rate=sample_rate,timestamp=timestamp
        ))

        position=None
        if form_estimate is not None:
            position=coordinate_from_listener_estimate(
                form_estimate,
                song_id=song_id or source_id,
                score_source_id=score_source_id,
                realchord_id=realchord_id,
                form_length_bars=form_length_bars,
                performance_phase=performance_phase,
                within_core_form=(form_length_bars is not None),
                provenance=("autonomous_listener","audio_evidence"),
            )

        row={
            "source_id":source_id,
            "sample_rate":sample_rate,
            "sample_count":len(payload)//4,
            "audio_evidence":_jsonable(evidence),
            "musical_position":_jsonable(position) if position is not None else None,
            "learning_status":(
                "canonical_coordinate_ready" if position is not None
                else "navigation_only"
            ),
            "provenance":[
                "browser_user_authorized_capture",
                "music_intelligence.audio_evidence",
                "listener_position_adapter",
            ],
        }
        self._append_jsonl(source_id,row)
        return row

    def _append_jsonl(self,source_id: str,row: dict) -> None:
        safe="".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in source_id)
        self.evidence_root.mkdir(parents=True,exist_ok=True)
        with (self.evidence_root/f"{safe}.jsonl").open("a",encoding="utf-8") as fh:
            fh.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
