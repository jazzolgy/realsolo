"""Source-separation boundary without coupling to a concrete model."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from ..adapters.source import AudioSource
from ..observation.models import SeparationMetadata


@dataclass(frozen=True)
class SeparatedSource:
    source: AudioSource
    metadata: SeparationMetadata

    def validate(self) -> None:
        self.source.validate()
        self.metadata.validate()


class SourceSeparator(Protocol):
    separator_id: str

    def separate(self, source: AudioSource) -> Sequence[SeparatedSource]:
        ...
