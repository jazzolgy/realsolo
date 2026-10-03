"""Bounded acoustic + musical-context posterior revision."""
from __future__ import annotations

from dataclasses import replace
from math import exp, log

from ..schemas.evidence import (
    AttributionFactor,
    AttributionRevision,
    AudioEventHypothesis,
    EventStatus,
    RevisionRecord,
)


class PosteriorAttributor:
    """Revise instrument ownership without allowing context to erase acoustics.

    Each context factor contributes a centered log-likelihood adjustment. The
    total contextual adjustment per candidate is clipped, so a weak acoustic
    prior cannot be converted into certainty by piling up plausibility rules.
    """

    def __init__(self, *, max_context_log_shift: float = 1.75) -> None:
        if max_context_log_shift <= 0.0:
            raise ValueError("max_context_log_shift must be positive")
        self.max_context_log_shift = float(max_context_log_shift)

    def revise(
        self,
        event: AudioEventHypothesis,
        factors: tuple[AttributionFactor, ...],
        *,
        revision_index: int = 1,
        reason: str = "musical_context_posterior_revision",
    ) -> AttributionRevision:
        event = event.normalized()
        prior = dict(event.instrument_probabilities)
        if not prior:
            raise ValueError("instrument_probabilities are required for attribution revision")

        labels = tuple(prior)
        shifts = {label: 0.0 for label in labels}
        provenance: list[str] = list(event.provenance)
        used_factors: list[str] = []

        for factor in factors:
            likelihoods = factor.normalized_likelihoods()
            shared = [label for label in labels if label in likelihoods]
            if not shared or factor.weight == 0.0:
                continue
            logs = {
                label: log(max(likelihoods.get(label, 1e-9), 1e-9))
                for label in labels
            }
            center = sum(logs.values()) / len(logs)
            for label in labels:
                shifts[label] += factor.weight * (logs[label] - center)
            used_factors.append(factor.factor)
            provenance.extend(factor.provenance)

        logits = {}
        for label, p in prior.items():
            bounded = max(
                -self.max_context_log_shift,
                min(self.max_context_log_shift, shifts[label]),
            )
            logits[label] = log(max(p, 1e-9)) + bounded

        peak = max(logits.values())
        raw = {label: exp(value - peak) for label, value in logits.items()}
        total = sum(raw.values())
        posterior = {label: value / total for label, value in raw.items()}

        ranked = sorted(posterior.items(), key=lambda kv: kv[1], reverse=True)
        top_label, top_p = ranked[0]
        runner_p = ranked[1][1] if len(ranked) > 1 else 0.0
        new_conf = replace(event.confidence, instrument=top_p)
        new_status = EventStatus.ATTRIBUTION_REVISED
        if top_p >= 0.90 and top_p - runner_p >= 0.25:
            new_status = EventStatus.CONFIRMED

        revised = replace(
            event,
            instrument_probabilities=posterior,
            confidence=new_conf,
            provenance=tuple(dict.fromkeys(provenance)),
            status=new_status,
        )
        record = RevisionRecord(
            event_id=event.event_id,
            revision_index=revision_index,
            previous_probabilities=prior,
            revised_probabilities=posterior,
            factors=tuple(used_factors),
            reason=reason,
            provenance=tuple(dict.fromkeys(provenance)),
        )
        return AttributionRevision(
            revised,
            record,
            top_label,
            top_p,
            runner_p,
        )
