"""Shared SoloRealizer interface and registry.

Shared Core never imports instrument implementations. Composition code registers
Player-owned realizers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from .solo_candidates import SoloCandidateSpec
from .solo_expression import SoloExpressionIntent


class SoloRealizer(Protocol):
    def realize(
        self,
        candidate: SoloCandidateSpec,
        expression: SoloExpressionIntent,
        context: Any,
    ) -> Any:
        ...


@dataclass
class SoloRealizerRegistry:
    _realizers: dict[str, SoloRealizer] = field(default_factory=dict)

    def register(self, instrument: str, realizer: SoloRealizer) -> None:
        key = instrument.strip().lower()
        if not key:
            raise ValueError("instrument is required")
        self._realizers[key] = realizer

    def get(self, instrument: str) -> SoloRealizer:
        key = instrument.strip().lower()
        if key not in self._realizers:
            raise KeyError(f"no solo realizer registered for {instrument!r}")
        return self._realizers[key]

    def realize(
        self,
        instrument: str,
        candidate: SoloCandidateSpec,
        expression: SoloExpressionIntent,
        context: Any,
    ) -> Any:
        candidate.validate()
        expression.validate()
        return self.get(instrument).realize(candidate, expression, context)
