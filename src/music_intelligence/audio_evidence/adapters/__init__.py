"""Adapters for source input and downstream contracts."""
from .local_audio import FFmpegSegmentMaterializer
from .performance_evidence import (
    PERFORMANCE_EVIDENCE_VERSION,
    to_performance_evidence_payload,
)
from .source import AudioSource

__all__ = [
    "AudioSource",
    "FFmpegSegmentMaterializer",
    "PERFORMANCE_EVIDENCE_VERSION",
    "to_performance_evidence_payload",
]
