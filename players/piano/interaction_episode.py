"""Experimental short interaction episodes for AI Pianist.

Episodes summarize only already-observed gesture/response exchanges. They never
contain a future action plan.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from .ensemble_response import (
    EnsembleActor,
    GestureResponseRecord,
    ResponseType,
)
from .variation import GestureSignature


class InteractionEpisodeType(str, Enum):
    OPEN_DIALOGUE = "open_dialogue"
    SOLOIST_LEAD = "soloist_lead"
    DENSITY_SHIFT = "density_shift"
    UNCLASSIFIED = "unclassified"


@dataclass(frozen=True)
class InteractionEpisode:
    episode_type: InteractionEpisodeType
    turns: tuple[GestureResponseRecord, ...]
    confidence: float
    active: bool = True

    def validate(self) -> None:
        if not self.turns:
            raise ValueError("interaction episode must contain at least one observed turn")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        for turn in self.turns:
            turn.validate()

    @property
    def last_gesture(self) -> GestureSignature:
        return self.turns[-1].gesture


@dataclass(frozen=True)
class EpisodeBias:
    total: float
    components: Mapping[str, float]
    reasons: tuple[str, ...]


def infer_interaction_episode(
    records: Sequence[GestureResponseRecord],
    *,
    max_turns: int = 4,
) -> InteractionEpisode | None:
    """Infer a tiny episode from recent observed history.

    Classification is descriptive and conservative. It does not predict the next
    musical event.
    """
    if max_turns < 1:
        raise ValueError("max_turns must be positive")
    if not records:
        return None

    turns = tuple(records[-max_turns:])
    for turn in turns:
        turn.validate()

    weighted = [
        t.observation.confidence * t.observation.attribution_confidence
        for t in turns
    ]
    confidence = sum(weighted) / len(weighted)

    rhythmic_dialogue = sum(
        1
        for t in turns
        if t.observation.response_type
        in {ResponseType.RHYTHMIC_ECHO, ResponseType.ACCENT_ALIGNMENT, ResponseType.SPACE_OPENED}
        and t.observation.attribution_confidence >= 0.35
    )
    soloist_lead = sum(
        1
        for t in turns
        if t.observation.actor is EnsembleActor.SOLOIST
        and t.observation.response_type is ResponseType.PHRASE_EXTENSION
    )
    density_shift = sum(
        1
        for t in turns
        if t.observation.response_type
        in {ResponseType.DENSITY_INCREASE, ResponseType.DENSITY_DECREASE}
    )

    if rhythmic_dialogue >= 2:
        episode_type = InteractionEpisodeType.OPEN_DIALOGUE
    elif soloist_lead >= 1:
        episode_type = InteractionEpisodeType.SOLOIST_LEAD
    elif density_shift >= 1:
        episode_type = InteractionEpisodeType.DENSITY_SHIFT
    else:
        episode_type = InteractionEpisodeType.UNCLASSIFIED

    trailing_no_response = 0
    for turn in reversed(turns):
        if turn.observation.response_type is ResponseType.NO_CLEAR_RESPONSE:
            trailing_no_response += 1
        else:
            break

    active = trailing_no_response < 2

    return InteractionEpisode(
        episode_type=episode_type,
        turns=turns,
        confidence=confidence,
        active=active,
    )


def evaluate_episode_bias(
    candidate: Any,
    episode: InteractionEpisode | None,
) -> EpisodeBias:
    """Apply a small current-candidate bias from the active observed episode."""
    if episode is None:
        return EpisodeBias(0.0, {}, ())
    episode.validate()
    if not episode.active or episode.confidence <= 0:
        return EpisodeBias(0.0, {}, ())

    current = GestureSignature.from_candidate(candidate)
    score = 0.0
    components: dict[str, float] = {}
    reasons: list[str] = []

    def add(key: str, value: float, reason: str) -> None:
        nonlocal score
        score += value
        components[key] = components.get(key, 0.0) + value
        reasons.append(reason)

    weight = episode.confidence

    if episode.episode_type is InteractionEpisodeType.OPEN_DIALOGUE:
        if current.role in {"answer", "punctuate"}:
            add(
                "dialogue_turn",
                0.08 * weight,
                "active dialogue episode supports an immediate answer/punctuation turn",
            )
        if (
            current.rhythm is not None
            and current.rhythm == episode.last_gesture.rhythm
        ):
            add(
                "dialogue_rhythm_identity",
                0.04 * weight,
                "dialogue can preserve a shared rhythmic identity while realization varies",
            )

    elif episode.episode_type is InteractionEpisodeType.SOLOIST_LEAD:
        if current.role == "lay_out":
            add(
                "soloist_lead_space",
                0.10 * weight,
                "soloist-led episode favors continued space",
            )
        elif current.role == "support":
            add(
                "soloist_lead_support",
                0.04 * weight,
                "soloist-led episode permits restrained support",
            )
        elif current.role in {"fill", "build"}:
            add(
                "soloist_lead_intrusion",
                -0.07 * weight,
                "fill/build can compete with an ongoing soloist-led episode",
            )

    elif episode.episode_type is InteractionEpisodeType.DENSITY_SHIFT:
        last_response = episode.turns[-1].observation.response_type
        if last_response is ResponseType.DENSITY_INCREASE:
            if current.role == "lay_out":
                add(
                    "density_shift_space",
                    0.08 * weight,
                    "recent density expansion favors recovery space",
                )
            if current.dynamic == "soft":
                add(
                    "density_shift_soft",
                    0.04 * weight,
                    "soft realization fits an expanded ensemble texture",
                )
        elif last_response is ResponseType.DENSITY_DECREASE:
            if current.role in {"support", "answer", "anchor"}:
                add(
                    "density_shift_reentry",
                    0.05 * weight,
                    "recent density reduction creates room for re-entry",
                )

    return EpisodeBias(score, components, tuple(reasons))
