"""Ambiguity summaries for Audio Evidence posterior audits."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..posterior.fusion import ContextualAudioHypothesis


@dataclass(frozen=True)
class AmbiguitySummary:
    total: int
    ambiguous: int
    ambiguous_fraction: float
    minimum_top_probability: float
    minimum_margin: float


def summarize_instrument_ambiguity(
    hypotheses: Iterable[ContextualAudioHypothesis],
    *,
    minimum_top_probability: float = 0.70,
    minimum_margin: float = 0.15,
) -> AmbiguitySummary:
    if not 0.0 <= minimum_top_probability <= 1.0:
        raise ValueError("minimum_top_probability must be within 0..1")
    if not 0.0 <= minimum_margin <= 1.0:
        raise ValueError("minimum_margin must be within 0..1")

    total = 0
    ambiguous = 0
    for hypothesis in hypotheses:
        ranking = hypothesis.instrument_ranking
        if not ranking:
            continue
        total += 1
        top = ranking[0][1]
        runner_up = ranking[1][1] if len(ranking) > 1 else 0.0
        if top < minimum_top_probability or top - runner_up < minimum_margin:
            ambiguous += 1

    fraction = ambiguous / total if total else 0.0
    return AmbiguitySummary(
        total=total,
        ambiguous=ambiguous,
        ambiguous_fraction=fraction,
        minimum_top_probability=minimum_top_probability,
        minimum_margin=minimum_margin,
    )
