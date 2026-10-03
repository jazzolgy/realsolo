"""Revision history and hard-example collection for posterior updates."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .fusion import ContextualAudioHypothesis


@dataclass(frozen=True)
class AttributionRevisionRecord:
    observation_id: str
    revision_index: int
    raw_instrument_probabilities: Mapping[str, float]
    posterior_instrument_probabilities: Mapping[str, float]
    factor_ids: tuple[str, ...]
    reason: str
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class HardExample:
    observation_id: str
    competing_instruments: tuple[str, ...]
    top_probability: float
    margin: float
    reason: str


@dataclass
class RevisionLedger:
    ambiguity_margin: float = 0.15
    minimum_top_probability: float = 0.70
    _history: dict[str, list[AttributionRevisionRecord]] = field(
        default_factory=dict
    )
    hard_examples: list[HardExample] = field(default_factory=list)

    def record(
        self,
        hypothesis: ContextualAudioHypothesis,
    ) -> AttributionRevisionRecord:
        observation = hypothesis.observation
        ranking = hypothesis.instrument_ranking
        top_probability = ranking[0][1] if ranking else 0.0
        runner_up = ranking[1][1] if len(ranking) > 1 else 0.0
        margin = top_probability - runner_up

        history = self._history.setdefault(observation.observation_id, [])
        revision = hypothesis.revision
        record = AttributionRevisionRecord(
            observation_id=observation.observation_id,
            revision_index=len(history) + 1,
            raw_instrument_probabilities=dict(
                observation.instrument_probabilities
            ),
            posterior_instrument_probabilities=dict(
                hypothesis.instrument_posterior
            ),
            factor_ids=revision.factor_ids if revision else (),
            reason=(
                revision.reason
                if revision
                else "posterior recorded without contextual revision"
            ),
            provenance=revision.provenance if revision else (),
        )
        history.append(record)

        if ranking and (
            top_probability < self.minimum_top_probability
            or margin < self.ambiguity_margin
        ):
            self.hard_examples.append(
                HardExample(
                    observation_id=observation.observation_id,
                    competing_instruments=tuple(
                        instrument for instrument, _ in ranking[:2]
                    ),
                    top_probability=top_probability,
                    margin=margin,
                    reason="instrument attribution remains ambiguous",
                )
            )
        return record

    def history_for(
        self,
        observation_id: str,
    ) -> tuple[AttributionRevisionRecord, ...]:
        return tuple(self._history.get(observation_id, ()))
