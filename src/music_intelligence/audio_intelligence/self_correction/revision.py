"""Revision history and hard-example collection."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..schemas.evidence import AttributionRevision, RevisionRecord


@dataclass(frozen=True)
class HardExample:
    source_id: str
    event_id: str
    competing_instruments: tuple[tuple[str, float], ...]
    reason: str
    provenance: tuple[str, ...] = ()


@dataclass
class RevisionLedger:
    ambiguity_margin: float = 0.15
    minimum_top_probability: float = 0.70
    records: list[RevisionRecord] = field(default_factory=list)
    hard_examples: list[HardExample] = field(default_factory=list)

    def record(self, revision: AttributionRevision) -> None:
        self.records.append(revision.record)
        if (
            revision.margin >= self.ambiguity_margin
            and revision.top_probability >= self.minimum_top_probability
        ):
            return
        ranked = tuple(sorted(
            (
                (k, float(v))
                for k, v in revision.event.instrument_probabilities.items()
            ),
            key=lambda kv: kv[1],
            reverse=True,
        )[:3])
        self.hard_examples.append(HardExample(
            source_id=revision.event.source_id,
            event_id=revision.event.event_id,
            competing_instruments=ranked,
            reason="ambiguous_instrument_attribution",
            provenance=revision.event.provenance,
        ))

    def history_for(self, event_id: str) -> tuple[RevisionRecord, ...]:
        return tuple(x for x in self.records if x.event_id == event_id)
