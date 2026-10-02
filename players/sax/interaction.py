"""Sax-specific interpretation of shared ensemble interaction directives."""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.reasoning.ensemble_state import InteractionKind
from music_intelligence.reasoning.interaction_scheduler import InteractionDirective

from .score_context import SaxScoreActivity, SaxScorePolicyContext


@dataclass(frozen=True)
class SaxInteractionDecision:
    interaction: InteractionKind = InteractionKind.NONE
    rest_bias: float = 0.0
    answer_bias: float = 0.0
    lead_bias: float = 0.0
    density_delta: float = 0.0
    suppress_free_improvisation: bool = False
    tags: frozenset[str] = frozenset()
    reasons: tuple[str, ...] = ()


def interpret_sax_interaction(
    directive: InteractionDirective | None,
    score: SaxScorePolicyContext,
) -> SaxInteractionDecision:
    interaction = directive.interaction if directive is not None else InteractionKind.NONE
    rest = 0.0
    answer = 0.0
    lead = 0.0
    density = directive.density_delta if directive is not None else 0.0
    tags = set(directive.tags if directive is not None else ())
    reasons = list(directive.reasons if directive is not None else ())

    suppress = score.activity in {
        SaxScoreActivity.HEAD_WRITTEN,
        SaxScoreActivity.WRITTEN_SOLO,
        SaxScoreActivity.WRITTEN_PART,
    }
    if suppress:
        reasons.append("written score role suppresses free-improvisation takeover")

    if interaction in {InteractionKind.HOLD_SPACE, InteractionKind.YIELD}:
        rest += .34
        reasons.append("ensemble directive favors space")
    elif interaction is InteractionKind.ANSWER:
        answer += .28
        reasons.append("ensemble directive opens answer window")
    elif interaction is InteractionKind.LEAD:
        lead += .18

    if score.phrase_boundary_after and interaction is InteractionKind.ANSWER:
        answer += .12
        tags.add("score_boundary_answer")
    if score.transition_bias > 0:
        rest += .08 * score.transition_bias
        tags.add("score_transition_sensitive")
    if score.activity is SaxScoreActivity.OPEN_SOLO and interaction is InteractionKind.LEAD:
        lead += .10
        tags.add("open_solo_lead")

    return SaxInteractionDecision(
        interaction=interaction,
        rest_bias=max(0.0, min(1.0, rest)),
        answer_bias=max(0.0, min(1.0, answer)),
        lead_bias=max(0.0, min(1.0, lead)),
        density_delta=max(-1.0, min(1.0, density)),
        suppress_free_improvisation=suppress,
        tags=frozenset(tags),
        reasons=tuple(reasons),
    )
