"""Source references consumed by the Audio Evidence Engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class AudioSource:
    source_id: str
    uri: str | None = None
    start_seconds: float | None = None
    end_seconds: float | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.start_seconds is not None and self.start_seconds < 0.0:
            raise ValueError("start_seconds may not be negative")
        if self.start_seconds is not None and self.end_seconds is not None and self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds must follow start_seconds")
