"""Soft intro-mode hypothesis updates."""
from __future__ import annotations

from .representation import (
    IntroMode,
    IntroModeHypothesis,
    IntroObservation,
    IntroState,
    clamp01,
    with_generation,
)


_EVIDENCE_FIELDS = {
    IntroMode.VOCAL_COUNT_IN: "vocal_count_confidence",
    IntroMode.INSTRUMENT_PICKUP: "pickup_confidence",
    IntroMode.RUBATO_SOLO: "rubato_confidence",
    IntroMode.PEDAL_POINT: "pedal_confidence",
    IntroMode.OSTINATO: "ostinato_confidence",
    IntroMode.GROOVE_VAMP: "vamp_confidence",
    IntroMode.WRITTEN_INTRO: "written_intro_confidence",
    IntroMode.FREE_COLLECTIVE: "free_collective_confidence",
    IntroMode.DIRECT_HEAD: "direct_head_confidence",
}


def update_intro_mode_hypotheses(
    state: IntroState,
    observation: IntroObservation,
) -> IntroState:
    """Bayes-like soft update without forcing a premature single label."""

    state.validate()
    observation.validate()
    prior = {h.mode: h.confidence for h in state.mode_hypotheses}
    raw: dict[IntroMode, float] = {}

    for mode, field in _EVIDENCE_FIELDS.items():
        evidence = float(getattr(observation, field))
        previous = prior.get(mode, 0.0)
        raw[mode] = 0.58 * previous + 0.42 * evidence + 0.02

    # UNKNOWN remains meaningful while evidence is weak or contradictory.
    strongest = max(raw.values(), default=0.0)
    prior_unknown = prior.get(IntroMode.UNKNOWN, 0.0)
    raw[IntroMode.UNKNOWN] = max(
        0.03,
        0.55 * prior_unknown + 0.45 * (1.0 - strongest),
    )

    total = sum(raw.values()) or 1.0
    normalized = tuple(
        IntroModeHypothesis(mode, clamp01(score / total))
        for mode, score in sorted(raw.items(), key=lambda item: item[1], reverse=True)
    )
    top = normalized[0].confidence if normalized else 0.0
    second = normalized[1].confidence if len(normalized) > 1 else 0.0
    ambiguity = clamp01(1.0 - max(0.0, top - second))

    return with_generation(
        state,
        mode_hypotheses=normalized,
        rubato_probability=clamp01(
            0.65 * state.rubato_probability + 0.35 * observation.rubato_confidence
        ),
        pickup_probability=clamp01(
            0.65 * state.pickup_probability + 0.35 * observation.pickup_confidence
        ),
        ambiguity=ambiguity,
        provenance=state.provenance + ("intro_mode_update",),
    )
