"""Experimental ensemble-response memory for AI Pianist.

This layer records what the ensemble did shortly after a committed piano gesture.
It does not claim causal certainty. Attribution confidence is explicit and may be low.

The concepts are likely instrument-independent and may later move to Shared Core.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from .variation import GestureSignature


class EnsembleActor(str, Enum):
    SOLOIST = "soloist"
    DRUMMER = "drummer"
    BASS = "bass"
    ENSEMBLE = "ensemble"


class ResponseType(str, Enum):
    RHYTHMIC_ECHO = "rhythmic_echo"
    ACCENT_ALIGNMENT = "accent_alignment"
    PHRASE_EXTENSION = "phrase_extension"
    PHRASE_END = "phrase_end"
    DENSITY_INCREASE = "density_increase"
    DENSITY_DECREASE = "density_decrease"
    SPACE_OPENED = "space_opened"
    HARMONIC_RESPONSE = "harmonic_response"
    NO_CLEAR_RESPONSE = "no_clear_response"


@dataclass(frozen=True)
class EnsembleResponseObservation:
    actor: EnsembleActor
    response_type: ResponseType
    strength: float = 0.5
    latency_beats: float = 0.0
    confidence: float = 1.0
    attribution_confidence: float = 0.5
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        for name in ("strength", "confidence", "attribution_confidence"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.latency_beats < 0:
            raise ValueError("latency_beats cannot be negative")


@dataclass(frozen=True)
class GestureResponseRecord:
    gesture: GestureSignature
    observation: EnsembleResponseObservation

    def validate(self) -> None:
        self.observation.validate()


@dataclass(frozen=True)
class EnsembleResponseBias:
    total: float
    components: Mapping[str, float]
    reasons: tuple[str, ...]


def evaluate_response_bias(
    candidate: Any,
    recent_responses: Sequence[GestureResponseRecord],
) -> EnsembleResponseBias:
    """Bias the current candidate using recent observed ensemble reactions.

    This is deliberately conservative: low attribution confidence has little effect,
    and no observation can force a particular action.
    """
    if not recent_responses:
        return EnsembleResponseBias(0.0, {}, ())

    current = GestureSignature.from_candidate(candidate)
    score = 0.0
    components: dict[str, float] = {}
    reasons: list[str] = []

    def add(key: str, value: float, reason: str) -> None:
        nonlocal score
        score += value
        components[key] = components.get(key, 0.0) + value
        reasons.append(reason)

    record = recent_responses[-1]
    record.validate()
    obs = record.observation
    weight = obs.strength * obs.confidence * obs.attribution_confidence

    if weight <= 0:
        return EnsembleResponseBias(0.0, {}, ())

    # Drummer/band echo: preserve some rhythmic identity without requiring literal
    # repetition of voicing/register/touch.
    if obs.response_type in {
        ResponseType.RHYTHMIC_ECHO,
        ResponseType.ACCENT_ALIGNMENT,
    }:
        if current.rhythm is not None and current.rhythm == record.gesture.rhythm:
            add(
                "responsive_groove_continuity",
                0.08 * weight,
                "recent ensemble rhythmic response supports preserving the rhythmic identity",
            )

    # If the soloist extends/increases after our gesture, make room rather than
    # interpreting that as permission to add more weight.
    if obs.actor is EnsembleActor.SOLOIST and obs.response_type is ResponseType.PHRASE_EXTENSION:
        if current.role == "lay_out":
            add(
                "soloist_extension_space",
                0.12 * weight,
                "soloist phrase extension favors giving the soloist continued space",
            )
        elif current.role == "support":
            add(
                "soloist_extension_support",
                0.05 * weight,
                "soloist phrase extension permits restrained support",
            )
        elif current.role in {"build", "fill"}:
            add(
                "soloist_extension_intrusion",
                -0.08 * weight,
                "soloist phrase extension argues against immediate build/fill pressure",
            )

    # A newly opened space can justify an answer/fill candidate.
    if obs.response_type in {ResponseType.PHRASE_END, ResponseType.SPACE_OPENED}:
        if current.role in {"answer", "fill", "punctuate"}:
            add(
                "response_window",
                0.10 * weight,
                "recent ensemble response opened a plausible dialogue window",
            )

    # Ensemble density increases after our action: reduce the next piano footprint.
    if obs.response_type is ResponseType.DENSITY_INCREASE:
        if current.role == "lay_out":
            add(
                "density_recovery",
                0.10 * weight,
                "ensemble density increase favors piano recovery space",
            )
        if current.dynamic == "soft":
            add(
                "density_softening",
                0.05 * weight,
                "soft realization reduces additional density after ensemble expansion",
            )
        if current.role == "build":
            add(
                "density_overbuild",
                -0.08 * weight,
                "further build risks compounding a recent ensemble density increase",
            )

    # Density decreases / space opens: restrained sound may re-enter.
    if obs.response_type is ResponseType.DENSITY_DECREASE:
        if current.role in {"support", "anchor", "answer"}:
            add(
                "reentry_opportunity",
                0.05 * weight,
                "ensemble density decrease creates room for restrained re-entry",
            )

    return EnsembleResponseBias(score, components, tuple(reasons))
