"""Detector interfaces; concrete models may be swapped independently."""
from __future__ import annotations

from typing import Protocol, Sequence

from ..adapters.source import AudioSource
from ..observation.models import AudioObservation


class AudioObservationDetector(Protocol):
    detector_id: str

    def detect(self, source: AudioSource) -> Sequence[AudioObservation]:
        ...
