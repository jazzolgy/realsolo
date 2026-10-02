"""v1.41 shared harmonic reasoning orchestrator.

This module composes the existing harmony layers into one current-moment
reasoning pass.  It does not replace the specialist modules and does not
generate instrument-specific notes or voicings.

Pipeline:
evidence frame -> competing interpretations -> modal/local-key context ->
contextual tension -> voice-leading -> reharmonization -> current affordances.

The output remains plural and auditable.  It may bias the next immediate
instrument action, but it never freezes a future chord or note sequence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .contextual_tension import TensionAssessment, TensionContext, assess_tension
from .harmonic_time import LocalKeyHypothesis, TonicizationEvidence, infer_local_key
from .hypothesis_engine import (
    EvidenceChannel,
    HarmonicHypothesis,
    HarmonicInterpretationSet,
    rank_harmonic_hypotheses,
)
from .jazz_harmony_core import (
    HarmonicAffordance,
    HarmonicFrame,
    HarmonicIntent,
    build_basic_affordances,
)
from .modal_nonfunctional import ModalAssessment, ModalState, assess_modal_state
from .reharmonization import (
    ReharmonizationAssessment,
    ReharmonizationProposal,
    assess_reharmonization,
)
from .voice_leading import (
    VoiceLeadingAssessment,
    VoiceLeadingContext,
    assess_voice_leading,
)


@dataclass(frozen=True)
class HarmonicReasoningInput:
    frame: HarmonicFrame
    hypotheses: tuple[HarmonicHypothesis, ...] = ()
    modal_state: ModalState | None = None
    tonicization_evidence: TonicizationEvidence | None = None
    tension_contexts: tuple[TensionContext, ...] = ()
    voice_leading_context: VoiceLeadingContext | None = None
    reharmonization_proposals: tuple[ReharmonizationProposal, ...] = ()
    channel_weights: Mapping[EvidenceChannel, float] | None = None


@dataclass(frozen=True)
class ReharmonizationResult:
    proposal: ReharmonizationProposal
    assessment: ReharmonizationAssessment


@dataclass(frozen=True)
class HarmonicActionOption:
    """Instrument-neutral current harmonic action family."""

    option_id: str
    source_affordance_id: str
    intent: HarmonicIntent
    harmonic_role: str
    weight: float
    confidence: float
    interpretation_compatibility: float
    context_tags: frozenset[str] = frozenset()
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class HarmonicReasoningResult:
    interpretations: HarmonicInterpretationSet
    modal: ModalAssessment | None
    local_key: LocalKeyHypothesis | None
    tensions: tuple[TensionAssessment, ...]
    voice_leading: VoiceLeadingAssessment | None
    reharmonizations: tuple[ReharmonizationResult, ...]
    base_affordances: tuple[HarmonicAffordance, ...]
    action_options: tuple[HarmonicActionOption, ...]
    uncertainty: float
    needs_more_evidence: bool


def _interpretation_compatibility(
    affordance: HarmonicAffordance,
    interpretations: HarmonicInterpretationSet,
) -> float:
    if not interpretations.ranked:
        return .5

    dominant_affordance = (
        "dominant" in affordance.harmonic_role
        or affordance.affordance_id.startswith("dominant.")
    )
    modal_affordance = "modal" in affordance.context_tags or "modal" in affordance.harmonic_role
    future_affordance = affordance.intent is HarmonicIntent.ANTICIPATE

    score = 0.0
    for ranked in interpretations.ranked:
        h = ranked.hypothesis
        family = h.interpretation_family.lower()
        function = (h.function or "").lower()
        compatible = .62

        if dominant_affordance:
            compatible = .95 if "dominant" in function or "dominant" in family else .38
        elif modal_affordance:
            compatible = .95 if "modal" in family else .42
        elif future_affordance:
            compatible = .78
        elif affordance.harmonic_role in {"voice_leading", "future_harmony"}:
            compatible = .82

        score += ranked.probability * compatible
    return max(0.0, min(1.0, score))


def _context_adjustment(
    affordance: HarmonicAffordance,
    *,
    modal: ModalAssessment | None,
    local_key: LocalKeyHypothesis | None,
    tensions: Sequence[TensionAssessment],
    voice_leading: VoiceLeadingAssessment | None,
    reharmonizations: Sequence[ReharmonizationResult],
    ambiguity: float,
) -> tuple[float, tuple[str, ...], frozenset[str]]:
    delta = 0.0
    reasons: list[str] = []
    tags = set(affordance.context_tags)

    if modal is not None and modal.modal_anchor_strength >= .6:
        tags.add("modal_anchor_strong")
        if "modal" in affordance.harmonic_role:
            delta += .10
            reasons.append("strong modal anchor")
        if affordance.intent is HarmonicIntent.REHARMONIZE:
            delta -= .03

    if local_key is not None:
        tags.add(f"key_region:{local_key.strength.value}")
        if local_key.support >= .62 and affordance.intent in {
            HarmonicIntent.CONNECT,
            HarmonicIntent.ANTICIPATE,
            HarmonicIntent.STABILIZE,
        }:
            delta += .05
            reasons.append("local-key target has sustained support")

    if tensions:
        mean_resolution = sum(t.resolution_need for t in tensions) / len(tensions)
        if mean_resolution >= .65 and affordance.intent in {
            HarmonicIntent.CONNECT,
            HarmonicIntent.STABILIZE,
        }:
            delta += .06
            reasons.append("active tension carries resolution pressure")
        if mean_resolution >= .65 and affordance.intent is HarmonicIntent.INTENSIFY:
            delta -= .03

    if voice_leading is not None:
        if voice_leading.debt_resolution_credit > 0 and affordance.intent in {
            HarmonicIntent.CONNECT,
            HarmonicIntent.STABILIZE,
        }:
            delta += .05
            reasons.append("candidate can pay resolution debt")
        if voice_leading.unresolved_debt_penalty > .08 and affordance.intent is HarmonicIntent.INTENSIFY:
            delta -= .04

    if reharmonizations and affordance.intent is HarmonicIntent.REHARMONIZE:
        best = max(x.assessment.continuity_score for x in reharmonizations)
        delta += .12 * (best - .5)
        reasons.append("reharmonization continuity evaluated")

    # Under high interpretive ambiguity, favor reversible / cross-compatible
    # actions and damp highly committal intensification.
    if ambiguity >= .65:
        tags.add("high_harmonic_ambiguity")
        if affordance.intent in {
            HarmonicIntent.CONNECT,
            HarmonicIntent.STABILIZE,
            HarmonicIntent.ANTICIPATE,
        }:
            delta += .04
            reasons.append("reversible action preferred under ambiguity")
        elif affordance.intent in {
            HarmonicIntent.INTENSIFY,
            HarmonicIntent.REHARMONIZE,
        }:
            delta -= .05

    return delta, tuple(reasons), frozenset(tags)


def reason_about_harmony(inp: HarmonicReasoningInput) -> HarmonicReasoningResult:
    inp.frame.validate()

    interpretations = rank_harmonic_hypotheses(
        inp.hypotheses,
        channel_weights=inp.channel_weights,
    )
    modal = assess_modal_state(inp.modal_state) if inp.modal_state is not None else None
    local_key = (
        infer_local_key(inp.tonicization_evidence)
        if inp.tonicization_evidence is not None
        else None
    )
    tensions = tuple(assess_tension(x) for x in inp.tension_contexts)
    voice_leading = (
        assess_voice_leading(inp.voice_leading_context)
        if inp.voice_leading_context is not None
        else None
    )
    reharmonizations = tuple(
        ReharmonizationResult(p, assess_reharmonization(p))
        for p in inp.reharmonization_proposals
    )

    affordances = build_basic_affordances(inp.frame)
    options: list[HarmonicActionOption] = []

    for a in affordances:
        compatibility = _interpretation_compatibility(a, interpretations)
        delta, reasons, tags = _context_adjustment(
            a,
            modal=modal,
            local_key=local_key,
            tensions=tensions,
            voice_leading=voice_leading,
            reharmonizations=reharmonizations,
            ambiguity=interpretations.ambiguity,
        )
        weight = a.weight + delta
        confidence = max(
            0.0,
            min(1.0, a.confidence * (.65 + .35 * compatibility)),
        )
        options.append(HarmonicActionOption(
            option_id=f"current:{a.affordance_id}",
            source_affordance_id=a.affordance_id,
            intent=a.intent,
            harmonic_role=a.harmonic_role,
            weight=weight,
            confidence=confidence,
            interpretation_compatibility=compatibility,
            context_tags=tags,
            reasons=reasons,
        ))

    # Reharmonization proposals become current optional action families only
    # when they have enough explanatory continuity.  They remain alternatives.
    for rr in reharmonizations:
        a = rr.assessment
        if a.continuity_score < .42:
            continue
        options.append(HarmonicActionOption(
            option_id=f"reharm:{rr.proposal.proposal_id}",
            source_affordance_id=rr.proposal.proposal_id,
            intent=HarmonicIntent.REHARMONIZE,
            harmonic_role=rr.proposal.kind.value,
            weight=.04 + .16 * a.continuity_score - .08 * a.risk,
            confidence=max(0.0, min(1.0, rr.proposal.confidence * a.continuity_score)),
            interpretation_compatibility=a.continuity_score,
            context_tags=frozenset({"reharmonization_candidate"}),
            reasons=a.reasons,
        ))

    options.sort(key=lambda x: (x.weight, x.confidence), reverse=True)

    uncertainty = interpretations.ambiguity
    if not inp.hypotheses:
        uncertainty = 1.0

    return HarmonicReasoningResult(
        interpretations=interpretations,
        modal=modal,
        local_key=local_key,
        tensions=tensions,
        voice_leading=voice_leading,
        reharmonizations=reharmonizations,
        base_affordances=affordances,
        action_options=tuple(options),
        uncertainty=uncertainty,
        needs_more_evidence=interpretations.needs_more_evidence,
    )
