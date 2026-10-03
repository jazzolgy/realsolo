"""Compare instrument-attribution systems without pretending to have ground truth."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from ..posterior.fusion import ContextualAudioHypothesis


@dataclass(frozen=True)
class AttributionSystemSummary:
    total: int
    covered: int
    ambiguous: int
    ambiguous_fraction: float
    average_top_probability: float


@dataclass(frozen=True)
class AttributionComparison:
    baseline: AttributionSystemSummary
    candidate: AttributionSystemSummary
    ambiguity_fraction_delta: float
    shared_observations: int
    top_label_disagreements: int


def _summarize(
    hypotheses: Sequence[ContextualAudioHypothesis],
    *,
    minimum_top_probability: float,
    minimum_margin: float,
) -> AttributionSystemSummary:
    total = len(hypotheses)
    covered = 0
    ambiguous = 0
    top_sum = 0.0

    for hypothesis in hypotheses:
        ranking = hypothesis.instrument_ranking
        if not ranking:
            continue
        covered += 1
        top = ranking[0][1]
        runner_up = ranking[1][1] if len(ranking) > 1 else 0.0
        top_sum += top
        if top < minimum_top_probability or top - runner_up < minimum_margin:
            ambiguous += 1

    return AttributionSystemSummary(
        total=total,
        covered=covered,
        ambiguous=ambiguous,
        ambiguous_fraction=(ambiguous / covered if covered else 0.0),
        average_top_probability=(top_sum / covered if covered else 0.0),
    )


def compare_instrument_attribution(
    baseline: Sequence[ContextualAudioHypothesis],
    candidate: Sequence[ContextualAudioHypothesis],
    *,
    minimum_top_probability: float = 0.70,
    minimum_margin: float = 0.15,
) -> AttributionComparison:
    baseline_summary = _summarize(
        baseline,
        minimum_top_probability=minimum_top_probability,
        minimum_margin=minimum_margin,
    )
    candidate_summary = _summarize(
        candidate,
        minimum_top_probability=minimum_top_probability,
        minimum_margin=minimum_margin,
    )

    baseline_by_id: Mapping[str, ContextualAudioHypothesis] = {
        item.observation.observation_id: item for item in baseline
    }
    candidate_by_id: Mapping[str, ContextualAudioHypothesis] = {
        item.observation.observation_id: item for item in candidate
    }
    shared_ids = sorted(set(baseline_by_id) & set(candidate_by_id))
    disagreements = 0
    for observation_id in shared_ids:
        left = baseline_by_id[observation_id].instrument_ranking
        right = candidate_by_id[observation_id].instrument_ranking
        if not left or not right:
            continue
        if left[0][0] != right[0][0]:
            disagreements += 1

    return AttributionComparison(
        baseline=baseline_summary,
        candidate=candidate_summary,
        ambiguity_fraction_delta=(
            candidate_summary.ambiguous_fraction
            - baseline_summary.ambiguous_fraction
        ),
        shared_observations=len(shared_ids),
        top_label_disagreements=disagreements,
    )
