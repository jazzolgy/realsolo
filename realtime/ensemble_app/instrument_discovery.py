"""Open-set instrument discovery for autonomous research listening.

Unknown instruments are not forced into the currently supported piano/bass/drums/sax
set. Repeated high-confidence evidence may promote a new instrument label into a
research profile candidate. Promotion does not automatically create a playable
runtime implementation; that remains a separate capability step.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence


@dataclass(frozen=True)
class InstrumentEvidence:
    source_id: str
    instrument_label: str
    family_label: str | None = None
    confidence: float = 0.0
    role_probabilities: Mapping[str, float] = field(default_factory=dict)
    occurrence_count: int = 1
    duration_s: float = 0.0

    def validate(self) -> None:
        if not self.instrument_label.strip():
            raise ValueError("instrument_label is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        if self.occurrence_count < 1:
            raise ValueError("occurrence_count must be >= 1")
        if self.duration_s < 0.0:
            raise ValueError("duration_s must be >= 0")


@dataclass(frozen=True)
class InstrumentPromotionPolicy:
    min_distinct_sources: int = 3
    min_total_occurrences: int = 12
    min_total_duration_s: float = 30.0
    min_mean_confidence: float = 0.78


@dataclass(frozen=True)
class InstrumentProfileCandidate:
    instrument_label: str
    family_label: str | None
    distinct_sources: int
    total_occurrences: int
    total_duration_s: float
    mean_confidence: float
    role_probabilities: Mapping[str, float]
    evidence_source_ids: tuple[str, ...]


def build_instrument_profile_candidate(
    evidence: Sequence[InstrumentEvidence],
    *,
    policy: InstrumentPromotionPolicy | None = None,
) -> InstrumentProfileCandidate | None:
    """Promote repeated evidence for one normalized instrument label.

    This is intentionally conservative: a single confident detector hit must never
    mutate the RealSolo instrument taxonomy.
    """

    if not evidence:
        return None
    policy = policy or InstrumentPromotionPolicy()
    for item in evidence:
        item.validate()

    labels={item.instrument_label.strip().lower() for item in evidence}
    if len(labels) != 1:
        raise ValueError("evidence must describe one normalized instrument label")

    sources=tuple(sorted({item.source_id for item in evidence if item.source_id}))
    total_occurrences=sum(item.occurrence_count for item in evidence)
    total_duration=sum(item.duration_s for item in evidence)
    weight=sum(max(1,item.occurrence_count) for item in evidence)
    mean_conf=sum(item.confidence*max(1,item.occurrence_count) for item in evidence)/weight

    if len(sources) < policy.min_distinct_sources:
        return None
    if total_occurrences < policy.min_total_occurrences:
        return None
    if total_duration < policy.min_total_duration_s:
        return None
    if mean_conf < policy.min_mean_confidence:
        return None

    role_totals: dict[str,float]={}
    role_weight=0.0
    for item in evidence:
        w=max(1,item.occurrence_count)*item.confidence
        role_weight += w
        for role,p in item.role_probabilities.items():
            role_totals[role]=role_totals.get(role,0.0)+w*float(p)
    normalized_roles=(
        {k:v/role_weight for k,v in sorted(role_totals.items())}
        if role_weight > 0 else {}
    )

    families=[item.family_label for item in evidence if item.family_label]
    family=max(set(families),key=families.count) if families else None

    return InstrumentProfileCandidate(
        instrument_label=next(iter(labels)),
        family_label=family,
        distinct_sources=len(sources),
        total_occurrences=total_occurrences,
        total_duration_s=total_duration,
        mean_confidence=mean_conf,
        role_probabilities=normalized_roles,
        evidence_source_ids=sources,
    )
