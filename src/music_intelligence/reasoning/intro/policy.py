"""Instrument-neutral intro entry policy.

This module decides the *degree of ensemble commitment*. It never chooses
instrument-specific pitches, voicings, stickings, articulations, or physical
technique.
"""
from __future__ import annotations

from dataclasses import replace

from .representation import EntryAction, EntryDecision, IntroState


def choose_entry_action(state: IntroState, decision: EntryDecision) -> EntryDecision:
    state.validate()

    r = decision.readiness
    p = decision.permission
    c = decision.confidence

    if p < 0.25 or r < 0.25:
        action = EntryAction.WAIT
    elif p < 0.45 or c < 0.38:
        action = EntryAction.SHADOW
    elif p < 0.62 or c < 0.55:
        action = EntryAction.LIGHT_SUPPORT
    elif p < 0.78 or c < 0.72:
        action = EntryAction.PARTIAL_JOIN
    else:
        action = EntryAction.FULL_JOIN

    # Strong unresolved rubato ambiguity makes a full ensemble entrance too
    # risky even when harmony is structurally ready.
    if (
        state.rubato_probability > 0.62
        and state.pulse_confidence < 0.58
        and action in {EntryAction.PARTIAL_JOIN, EntryAction.FULL_JOIN}
    ):
        action = EntryAction.LIGHT_SUPPORT

    out = replace(decision, action=action)
    out.validate()
    return out
