"""Piano solo policy using bebop melodic priors.

Charlie Parker is the first default melodic LegendProfile, not the identity of the
piano player. The profile biases immediate note decisions; piano realization,
register, touch, and accompaniment interaction remain instrument-local.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from music_intelligence.bebop.parker_online_profile import PARKER_ONLINE_PROFILE
from music_intelligence.reasoning.legend_style_core import (
    CandidateEvent,
    CandidateScore,
    LegendBlend,
    MusicalContextVector,
)
from music_intelligence.reasoning.online_improviser import (
    OnlineMusicalEvaluator,
    PerformanceMemory,
    SoftPlan,
)


def default_bebop_legend_blend() -> LegendBlend:
    return LegendBlend(((PARKER_ONLINE_PROFILE, 1.0),))


@dataclass(frozen=True)
class PianoSoloContext:
    musical: MusicalContextVector = field(default_factory=MusicalContextVector)
    right_hand_low_midi: int = 48
    right_hand_high_midi: int = 96
    left_hand_comping_activity: float = 0.35
    ensemble_density: float = 0.5
    creativity_strength: float = 0.6

    def validate(self) -> None:
        if not 21 <= self.right_hand_low_midi <= 108:
            raise ValueError("right_hand_low_midi outside piano range")
        if not 21 <= self.right_hand_high_midi <= 108:
            raise ValueError("right_hand_high_midi outside piano range")
        if self.right_hand_low_midi >= self.right_hand_high_midi:
            raise ValueError("right-hand range must be ascending")
        for name in (
            "left_hand_comping_activity",
            "ensemble_density",
            "creativity_strength",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


@dataclass
class PianoSoloState:
    memory: PerformanceMemory = field(default_factory=PerformanceMemory)

    @property
    def previous_pitch_midi(self) -> int | None:
        for event in reversed(self.memory.committed):
            if event.pitch_midi is not None:
                return event.pitch_midi
        return None


class PianoSoloEvaluator:
    """Immediate monophonic piano-solo evaluator.

    Shared bebop/legend logic remains generic. This layer only adds piano-local
    constraints and accompaniment-space considerations.
    """

    def __init__(self, legend_blend: LegendBlend | None = None):
        self.legend_blend = legend_blend or default_bebop_legend_blend()
        self.shared = OnlineMusicalEvaluator(self.legend_blend)

    def evaluate(
        self,
        candidate: CandidateEvent,
        context: PianoSoloContext,
    ) -> CandidateScore:
        context.validate()
        base = self.shared.evaluate(candidate, context.musical)

        score = base.total
        components = dict(base.components)
        reasons = list(base.reasons)

        if candidate.pitch_midi is not None:
            if not 21 <= candidate.pitch_midi <= 108:
                components["piano_range"] = -10.0
                reasons.append("candidate lies outside physical piano range")
                return CandidateScore(candidate, score - 10.0, components, tuple(reasons))

            if not (
                context.right_hand_low_midi
                <= candidate.pitch_midi
                <= context.right_hand_high_midi
            ):
                components["right_hand_register"] = -0.18
                score -= 0.18
                reasons.append("candidate leaves preferred right-hand solo register")

        tags = set(candidate.tags)

        # Busy LH/ensemble texture should redirect the solo toward clarity, not
        # suppress melodic creativity entirely.
        if (
            context.left_hand_comping_activity >= 0.7
            or context.ensemble_density >= 0.75
        ):
            if "rest" in tags or candidate.pitch_midi is None:
                components["texture_space"] = 0.12
                score += 0.12
                reasons.append("space protects clarity over busy accompaniment")
            if "dense_run" in tags:
                components["texture_crowding"] = -0.12
                score -= 0.12
                reasons.append("dense run competes with active accompaniment")

        # Bebop is the initial priority: directed chromaticism is favored more than
        # undirected chromatic saturation.
        if {"close_approach", "neighbor", "passing"} & tags:
            components["piano_bebop_connector"] = 0.05
            score += 0.05
            reasons.append("bebop connector remains idiomatic on piano")

        if "altered" in tags and not (
            {"directed_target", "resolution_path"} & tags
        ):
            components["undirected_chromaticism"] = -0.08
            score -= 0.08
            reasons.append("chromatic color lacks an audible target or return path")

        return CandidateScore(candidate, score, components, tuple(reasons))

    def choose_immediate(
        self,
        candidates: Sequence[CandidateEvent],
        context: PianoSoloContext,
    ) -> CandidateScore:
        if not candidates:
            raise ValueError("no piano solo candidates")
        return max(
            (self.evaluate(candidate, context) for candidate in candidates),
            key=lambda item: item.total,
        )


def perform_one_piano_solo_event(
    plan: SoftPlan,
    evaluator: PianoSoloEvaluator,
    candidates: Sequence[CandidateEvent],
    context: PianoSoloContext,
    state: PianoSoloState,
) -> CandidateScore:
    """Choose and commit one immediate solo event, then the system must re-listen."""
    plan.validate_for_improvisation()
    chosen = evaluator.choose_immediate(candidates, context)
    state.memory.commit(chosen.candidate)
    return chosen
