"""Diagnostics for raw-observation vs contextual-posterior disagreement.

These metrics do not decide musical truth. They quantify how strongly context
changed an acoustic interpretation so downstream systems can calibrate,
debug, or request review without discarding either evidence layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .events import CommittedPerformanceEvent, ProbabilityEstimate


class CorrectionRiskLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True)
class CorrectionRiskPolicy:
    """Configurable thresholds; values are product policy, not musical truth."""

    moderate_tv_distance: float = 0.20
    high_tv_distance: float = 0.45
    context_dominated_posterior: float = 0.75
    context_dominated_raw_support: float = 0.35
    high_context_lift: float = 0.40

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.high_tv_distance < self.moderate_tv_distance:
            raise ValueError("high_tv_distance must be >= moderate_tv_distance")


@dataclass(frozen=True)
class DistributionShift:
    domain: str
    tv_distance: float
    raw_top_label: str | None
    raw_top_probability: float | None
    posterior_top_label: str | None
    posterior_top_probability: float | None
    posterior_label_raw_support: float | None
    posterior_label_lift: float | None
    top_label_changed: bool
    context_dominated: bool
    risk_level: CorrectionRiskLevel
    review_recommended: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class EventCorrectionReport:
    event_id: str
    instrument_shift: DistributionShift | None = None
    role_shift: DistributionShift | None = None

    @property
    def review_recommended(self) -> bool:
        return any(
            shift is not None and shift.review_recommended
            for shift in (self.instrument_shift, self.role_shift)
        )

    @property
    def max_risk(self) -> CorrectionRiskLevel:
        order = {
            CorrectionRiskLevel.NONE: 0,
            CorrectionRiskLevel.LOW: 1,
            CorrectionRiskLevel.MODERATE: 2,
            CorrectionRiskLevel.HIGH: 3,
        }
        shifts = [s for s in (self.instrument_shift, self.role_shift) if s is not None]
        if not shifts:
            return CorrectionRiskLevel.NONE
        return max((s.risk_level for s in shifts), key=order.__getitem__)


def _as_map(items: Iterable[ProbabilityEstimate]) -> dict[str, float]:
    result: dict[str, float] = {}
    for item in items:
        item.validate()
        result[item.label] = result.get(item.label, 0.0) + item.probability
    return result


def total_variation_distance(
    raw: tuple[ProbabilityEstimate, ...],
    posterior: tuple[ProbabilityEstimate, ...],
) -> float:
    """Return categorical total-variation distance in [0, 1].

    Missing labels are treated as zero probability. Empty distributions have
    no measurable shift and return 0.
    """

    if not raw and not posterior:
        return 0.0
    raw_map = _as_map(raw)
    posterior_map = _as_map(posterior)
    labels = set(raw_map) | set(posterior_map)
    return 0.5 * sum(abs(raw_map.get(k, 0.0) - posterior_map.get(k, 0.0)) for k in labels)


def _top(values: dict[str, float]) -> tuple[str | None, float | None]:
    if not values:
        return None, None
    label, probability = max(values.items(), key=lambda kv: (kv[1], kv[0]))
    return label, probability


def analyze_distribution_shift(
    domain: str,
    raw: tuple[ProbabilityEstimate, ...],
    posterior: tuple[ProbabilityEstimate, ...],
    *,
    policy: CorrectionRiskPolicy = CorrectionRiskPolicy(),
) -> DistributionShift | None:
    """Measure context correction without declaring the posterior correct/incorrect."""

    policy.validate()
    if not raw or not posterior:
        return None

    raw_map = _as_map(raw)
    posterior_map = _as_map(posterior)
    raw_label, raw_p = _top(raw_map)
    post_label, post_p = _top(posterior_map)
    assert post_label is not None and post_p is not None

    raw_support = raw_map.get(post_label, 0.0)
    lift = post_p - raw_support
    tv = total_variation_distance(raw, posterior)
    changed = raw_label != post_label

    dominated = (
        post_p >= policy.context_dominated_posterior
        and raw_support <= policy.context_dominated_raw_support
        and lift >= policy.high_context_lift
    )

    reasons: list[str] = []
    if changed:
        reasons.append("top_label_changed")
    if tv >= policy.high_tv_distance:
        reasons.append("large_distribution_shift")
    elif tv >= policy.moderate_tv_distance:
        reasons.append("moderate_distribution_shift")
    if dominated:
        reasons.append("context_dominated_posterior")

    if dominated or (changed and tv >= policy.high_tv_distance):
        risk = CorrectionRiskLevel.HIGH
    elif changed or tv >= policy.moderate_tv_distance:
        risk = CorrectionRiskLevel.MODERATE
    elif tv > 0:
        risk = CorrectionRiskLevel.LOW
    else:
        risk = CorrectionRiskLevel.NONE

    return DistributionShift(
        domain=domain,
        tv_distance=tv,
        raw_top_label=raw_label,
        raw_top_probability=raw_p,
        posterior_top_label=post_label,
        posterior_top_probability=post_p,
        posterior_label_raw_support=raw_support,
        posterior_label_lift=lift,
        top_label_changed=changed,
        context_dominated=dominated,
        risk_level=risk,
        review_recommended=risk is CorrectionRiskLevel.HIGH,
        reasons=tuple(reasons),
    )


def analyze_event_correction(
    event: CommittedPerformanceEvent,
    *,
    policy: CorrectionRiskPolicy = CorrectionRiskPolicy(),
) -> EventCorrectionReport:
    """Analyze instrument/role correction magnitude for one evidence event."""

    event.validate()
    return EventCorrectionReport(
        event_id=event.event_id,
        instrument_shift=analyze_distribution_shift(
            "instrument",
            event.raw_instrument_probabilities,
            event.context_instrument_probabilities,
            policy=policy,
        ),
        role_shift=analyze_distribution_shift(
            "role",
            event.raw_role_probabilities,
            event.context_role_probabilities,
            policy=policy,
        ),
    )
