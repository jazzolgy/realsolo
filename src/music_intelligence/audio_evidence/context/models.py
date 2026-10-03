"""Context evidence used only to disambiguate audio observations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ContextEvidence:
    factor_id: str
    likelihoods: Mapping[str, float]
    weight: float = 1.0
    source: str = "audio-context"

    def validate(self) -> None:
        if not self.factor_id:
            raise ValueError("factor_id is required")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("weight must be within 0..1")
        if not self.likelihoods:
            raise ValueError("likelihoods are required")
        for key, value in self.likelihoods.items():
            if not key or value <= 0.0:
                raise ValueError("context likelihoods require non-empty keys and positive values")
