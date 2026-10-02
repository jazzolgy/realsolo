"""v1.40 harmonic interpretation candidates.

Harmony is not forced into one analysis. Expected / Observed / Inferred
evidence remain separate, and multiple harmonic hypotheses may coexist with
independent confidence components and provenance.

This follows the project-wide Interpretation Candidates principle and the
uploaded modal-harmony material's warning that the same upper structure can be
heard differently depending on bass/context.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import log
from typing import Mapping, Sequence


class EvidenceChannel(str, Enum):
    EXPECTED = "expected"
    OBSERVED = "observed"
    INFERRED = "inferred"
    VOICE_LEADING = "voice_leading"
    BASS = "bass"
    MELODY = "melody"
    HARMONIC_TIME = "harmonic_time"
    MODAL_CONTEXT = "modal_context"
    FORM = "form"
    HUMAN = "human"


@dataclass(frozen=True)
class ConfidenceVector:
    expected: float = 0.0
    observed: float = 0.0
    inferred: float = 0.0
    voice_leading: float = 0.0
    bass: float = 0.0
    melody: float = 0.0
    harmonic_time: float = 0.0
    modal_context: float = 0.0
    form: float = 0.0
    human: float = 0.0

    def validate(self) -> None:
        for value in self.__dict__.values():
            if not 0.0 <= value <= 1.0:
                raise ValueError("confidence components must be within 0..1")

    def weighted(self, weights: Mapping[EvidenceChannel, float] | None = None) -> float:
        self.validate()
        values = {
            EvidenceChannel.EXPECTED: self.expected,
            EvidenceChannel.OBSERVED: self.observed,
            EvidenceChannel.INFERRED: self.inferred,
            EvidenceChannel.VOICE_LEADING: self.voice_leading,
            EvidenceChannel.BASS: self.bass,
            EvidenceChannel.MELODY: self.melody,
            EvidenceChannel.HARMONIC_TIME: self.harmonic_time,
            EvidenceChannel.MODAL_CONTEXT: self.modal_context,
            EvidenceChannel.FORM: self.form,
            EvidenceChannel.HUMAN: self.human,
        }
        active = {k: v for k, v in values.items() if v > 0}
        if not active:
            return 0.0
        if weights is None:
            return sum(active.values()) / len(active)
        numerator = sum(v * max(0.0, weights.get(k, 1.0)) for k, v in active.items())
        denominator = sum(max(0.0, weights.get(k, 1.0)) for k in active)
        return numerator / denominator if denominator else 0.0


@dataclass(frozen=True)
class HarmonicHypothesis:
    hypothesis_id: str
    label: str
    root_pc: int | None = None
    function: str | None = None
    key_or_mode: str | None = None
    interpretation_family: str = "unknown"
    confidence: ConfidenceVector = ConfidenceVector()
    evidence: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    human_correction: str | None = None

    def validate(self) -> None:
        if not self.hypothesis_id:
            raise ValueError("hypothesis_id is required")
        if self.root_pc is not None and not 0 <= self.root_pc <= 11:
            raise ValueError("root_pc must be in 0..11")
        self.confidence.validate()


@dataclass(frozen=True)
class RankedHypothesis:
    hypothesis: HarmonicHypothesis
    score: float
    probability: float
    contradiction_penalty: float


@dataclass(frozen=True)
class HarmonicInterpretationSet:
    ranked: tuple[RankedHypothesis, ...]
    ambiguity: float
    top_margin: float
    needs_more_evidence: bool

    @property
    def preferred(self) -> HarmonicHypothesis | None:
        return self.ranked[0].hypothesis if self.ranked else None

    @property
    def alternatives(self) -> tuple[HarmonicHypothesis, ...]:
        return tuple(x.hypothesis for x in self.ranked[1:])


def _softmax(scores: Sequence[float], temperature: float) -> tuple[float, ...]:
    if not scores:
        return ()
    t = max(1e-6, temperature)
    m = max(scores)
    exps = [pow(2.718281828459045, (x - m) / t) for x in scores]
    total = sum(exps)
    return tuple(x / total for x in exps)


def _entropy(probabilities: Sequence[float]) -> float:
    if len(probabilities) <= 1:
        return 0.0
    h = -sum(p * log(p) for p in probabilities if p > 0)
    return h / log(len(probabilities))


def rank_harmonic_hypotheses(
    hypotheses: Sequence[HarmonicHypothesis],
    *,
    channel_weights: Mapping[EvidenceChannel, float] | None = None,
    contradiction_cost: float = .08,
    temperature: float = .18,
    ambiguity_threshold: float = .58,
    margin_threshold: float = .14,
) -> HarmonicInterpretationSet:
    if not hypotheses:
        return HarmonicInterpretationSet((), 0.0, 0.0, True)

    raw: list[tuple[HarmonicHypothesis, float, float]] = []
    for h in hypotheses:
        h.validate()
        base = h.confidence.weighted(channel_weights)
        penalty = min(.45, contradiction_cost * len(h.contradictions))
        score = max(0.0, min(1.0, base - penalty))
        raw.append((h, score, penalty))

    probabilities = _softmax([x[1] for x in raw], temperature)
    ranked = sorted(
        (
            RankedHypothesis(h, score, p, penalty)
            for (h, score, penalty), p in zip(raw, probabilities)
        ),
        key=lambda x: x.probability,
        reverse=True,
    )

    ambiguity = _entropy([x.probability for x in ranked])
    margin = (
        ranked[0].probability - ranked[1].probability
        if len(ranked) > 1
        else 1.0
    )
    needs_more = ambiguity >= ambiguity_threshold or margin <= margin_threshold

    return HarmonicInterpretationSet(
        tuple(ranked),
        ambiguity,
        margin,
        needs_more,
    )


def merge_human_correction(
    hypothesis: HarmonicHypothesis,
    *,
    correction: str,
    confidence: float = 1.0,
) -> HarmonicHypothesis:
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be within 0..1")
    c = hypothesis.confidence
    return HarmonicHypothesis(
        hypothesis_id=hypothesis.hypothesis_id,
        label=hypothesis.label,
        root_pc=hypothesis.root_pc,
        function=hypothesis.function,
        key_or_mode=hypothesis.key_or_mode,
        interpretation_family=hypothesis.interpretation_family,
        confidence=ConfidenceVector(
            expected=c.expected,
            observed=c.observed,
            inferred=c.inferred,
            voice_leading=c.voice_leading,
            bass=c.bass,
            melody=c.melody,
            harmonic_time=c.harmonic_time,
            modal_context=c.modal_context,
            form=c.form,
            human=confidence,
        ),
        evidence=hypothesis.evidence,
        contradictions=hypothesis.contradictions,
        provenance=hypothesis.provenance + ("human_correction",),
        human_correction=correction,
    )
