"""Bass performance-expression realization v0.1.

Transforms an immediate bass candidate plus its metric/interaction context into
performance parameters. This is deliberately separate from note identity:

- notated duration stays on CandidateEvent;
- sounding length is a performance ratio;
- accent is independent from harmonic importance;
- microtiming is a small local offset around the shared pulse;
- ghost/dead-note behavior is represented first as an opportunity score rather
  than blindly inserting extra notes.

The initial values are interpretable heuristics for testing the architecture,
not claims of measured universal bebop constants.
"""
from __future__ import annotations

from dataclasses import dataclass

from .interaction_grammar import BassInteractionDecision, BassInteractionIntent
from .performance_grammar import (
    ArticulationIntent,
    BassGrammarDecision,
    MetricRole,
)
from .performance_memory import BassArticulation, BassPerformanceSnapshot


@dataclass(frozen=True)
class BassExpressionProfile:
    sounding_length_ratio: float
    accent: float
    microtiming_ms: float
    articulation: BassArticulation
    ghost_opportunity: float = 0.0
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        if not 0.0 <= self.sounding_length_ratio <= 1.5:
            raise ValueError("sounding_length_ratio must be within 0..1.5")
        if not 0.0 <= self.accent <= 1.0:
            raise ValueError("accent must be within 0..1")
        if not -60.0 <= self.microtiming_ms <= 60.0:
            raise ValueError("microtiming_ms must remain a local pulse adjustment")
        if not 0.0 <= self.ghost_opportunity <= 1.0:
            raise ValueError("ghost_opportunity must be within 0..1")


def realize_bass_expression(
    *,
    mode: str,
    grammar: BassGrammarDecision,
    memory: BassPerformanceSnapshot = BassPerformanceSnapshot(),
    interaction: BassInteractionDecision | None = None,
) -> BassExpressionProfile:
    """Realize how the already-chosen immediate bass event should be played."""
    reasons: list[str] = []

    if mode == "two_feel":
        length = .94
        accent = .56
        timing = 0.0
    elif mode == "pedal":
        length = 1.02
        accent = .54
        timing = 0.0
    else:
        length = .86
        accent = .52
        timing = 0.0

    articulation = BassArticulation.NEUTRAL
    ghost = 0.0

    if grammar.articulation_intent is ArticulationIntent.CONNECTED:
        articulation = BassArticulation.CONNECTED
        length += .05
        reasons.append("directed connection uses a more connected note body")
    elif grammar.articulation_intent is ArticulationIntent.SHORT:
        articulation = BassArticulation.SHORT
        length -= .20

    if grammar.metric_role is MetricRole.HARMONIC_ANCHOR:
        accent += .07
        reasons.append("harmonic anchor receives modest attack definition")
    elif grammar.metric_role is MetricRole.PREPARATION:
        accent -= .03
        reasons.append("preparation need not overpower the following arrival")
        ghost += .10
    elif grammar.metric_role is MetricRole.TWO_FEEL_ANCHOR:
        length += .02

    if interaction is not None:
        intent = interaction.intent

        if intent in {
            BassInteractionIntent.ANCHOR,
            BassInteractionIntent.HOLD,
            BassInteractionIntent.RESET,
        }:
            length += .04
            accent += .02
            timing += 1.0
            reasons.append(f"{intent.value} stabilizes note body and pulse")

        elif intent is BassInteractionIntent.YIELD:
            accent -= .08
            length -= .05
            timing += 3.0
            reasons.append("yield reduces foreground attack")

        elif intent in {
            BassInteractionIntent.PROPEL,
            BassInteractionIntent.BUILD,
        }:
            accent += .08
            timing -= 4.0
            ghost += .05
            reasons.append(f"{intent.value} adds forward attack energy")

        elif intent in {
            BassInteractionIntent.CONNECT,
            BassInteractionIntent.ANSWER,
        }:
            articulation = BassArticulation.CONNECTED
            length += .04
            accent += .03
            timing -= 2.0
            ghost += .08
            reasons.append(f"{intent.value} favors connected directional delivery")

        elif intent is BassInteractionIntent.RELEASE:
            accent -= .05
            length -= .04
            reasons.append("release softens the local attack")

        elif intent is BassInteractionIntent.FILL:
            accent += .05
            ghost += .14
            timing -= 3.0
            reasons.append("fill opens limited ornamental articulation")

        ghost += max(0.0, interaction.response_opportunity - .45) * .20
        if interaction.complexity_delta < 0:
            ghost += interaction.complexity_delta * .18

    # Recent articulation/complexity creates a restraint budget.
    if memory.recent_ghost_count >= 1:
        ghost -= .16 * min(2, memory.recent_ghost_count)
        reasons.append("recent ghost/dead notes create articulation restraint")
    if memory.recent_complexity >= .62:
        ghost -= .12
        accent -= .02
        reasons.append("recent complexity favors plainer articulation")

    # Accent should breathe rather than converge on a constant value.
    if memory.recent_accent_mean >= .66:
        accent -= .04
        reasons.append("recent strong attacks create accent-release pressure")
    elif memory.recent_accent_mean <= .38:
        accent += .03

    length = max(.25, min(1.10, length))
    accent = max(.15, min(.88, accent))
    timing = max(-12.0, min(12.0, timing))
    ghost = max(0.0, min(.45, ghost))

    if articulation is BassArticulation.NEUTRAL and length <= .64:
        articulation = BassArticulation.SHORT

    profile = BassExpressionProfile(
        sounding_length_ratio=length,
        accent=accent,
        microtiming_ms=timing,
        articulation=articulation,
        ghost_opportunity=ghost,
        reasons=tuple(reasons),
    )
    profile.validate()
    return profile
