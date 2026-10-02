"""Phrase-level intention for the canonical Bass player.

This layer owns bass performance policy, not shared form/harmony analysis.
It turns Shared Core phrase/form/ensemble cues plus committed bass memory into
a persistent short-horizon intention.

It never precomposes future notes. The intention is re-evaluated after every
committed action.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .interaction_grammar import BassInteractionDecision, BassInteractionIntent
from .performance_memory import BassPerformanceSnapshot


class BassPhraseIntentKind(str, Enum):
    GROUND = "ground"
    DEVELOP = "develop"
    BUILD = "build"
    SUSTAIN = "sustain"
    RELEASE = "release"
    RESET = "reset"


class BassPhraseDirection(str, Enum):
    STABLE = "stable"
    RISE = "rise"
    FALL = "fall"
    RECOVER = "recover"


@dataclass(frozen=True)
class BassPhraseIntent:
    kind: BassPhraseIntentKind
    direction: BassPhraseDirection = BassPhraseDirection.STABLE
    complexity_target: float = .35
    information_density_target: float = .45
    articulation_energy: float = .50
    persistence: int = 3
    reasons: tuple[str, ...] = ()


@dataclass
class BassPhraseState:
    current: BassPhraseIntent = BassPhraseIntent(BassPhraseIntentKind.GROUND)
    committed_under_intent: int = 0

    def commit(self) -> None:
        self.committed_under_intent += 1

    def replace(self, intent: BassPhraseIntent) -> None:
        self.current = intent
        self.committed_under_intent = 0


@dataclass(frozen=True)
class BassPhraseContext:
    memory: BassPerformanceSnapshot = BassPerformanceSnapshot()
    interaction: BassInteractionDecision | None = None
    phrase_boundary: bool = False
    form_boundary: bool = False
    soloist_phrase_ending: bool = False
    phrase_progress: float | None = None
    ensemble_activity: float = .5

    def validate(self) -> None:
        if self.phrase_progress is not None and not 0.0 <= self.phrase_progress <= 1.0:
            raise ValueError("phrase_progress must be within 0..1")
        if not 0.0 <= self.ensemble_activity <= 1.0:
            raise ValueError("ensemble_activity must be within 0..1")


def choose_bass_phrase_intent(
    ctx: BassPhraseContext,
    *,
    previous: BassPhraseIntent | None = None,
    actions_under_previous: int = 0,
) -> BassPhraseIntent:
    ctx.validate()
    reasons: list[str] = []

    if ctx.form_boundary:
        return BassPhraseIntent(
            BassPhraseIntentKind.RESET,
            BassPhraseDirection.RECOVER,
            complexity_target=.18,
            information_density_target=.28,
            articulation_energy=.42,
            persistence=2,
            reasons=("form boundary requests re-orientation",),
        )

    if ctx.phrase_boundary:
        return BassPhraseIntent(
            BassPhraseIntentKind.RELEASE,
            BassPhraseDirection.RECOVER,
            complexity_target=.20,
            information_density_target=.30,
            articulation_energy=.38,
            persistence=2,
            reasons=("phrase boundary requests release before rebuilding",),
        )

    if ctx.soloist_phrase_ending:
        reasons.append("soloist phrase ending opens a response/release window")
        if ctx.interaction is not None and ctx.interaction.intent in {
            BassInteractionIntent.ANSWER,
            BassInteractionIntent.CONNECT,
        }:
            return BassPhraseIntent(
                BassPhraseIntentKind.DEVELOP,
                BassPhraseDirection.RISE,
                complexity_target=.52,
                information_density_target=.56,
                articulation_energy=.58,
                persistence=3,
                reasons=tuple(reasons + ["ensemble leaves room for bass response"]),
            )
        return BassPhraseIntent(
            BassPhraseIntentKind.RELEASE,
            BassPhraseDirection.STABLE,
            complexity_target=.24,
            information_density_target=.30,
            articulation_energy=.40,
            persistence=2,
            reasons=tuple(reasons),
        )

    # Explicit phrase progress from Shared Core overrides local heuristics.
    if ctx.phrase_progress is not None:
        p = ctx.phrase_progress
        if p < .20:
            return BassPhraseIntent(
                BassPhraseIntentKind.GROUND,
                BassPhraseDirection.STABLE,
                .25, .36, .46, 3,
                ("early phrase favors orientation",),
            )
        if p < .58:
            return BassPhraseIntent(
                BassPhraseIntentKind.DEVELOP,
                BassPhraseDirection.RISE,
                .48, .52, .55, 4,
                ("middle phrase supports gradual development",),
            )
        if p < .82:
            return BassPhraseIntent(
                BassPhraseIntentKind.BUILD,
                BassPhraseDirection.RISE,
                .62, .62, .64, 3,
                ("late-middle phrase supports a controlled build",),
            )
        return BassPhraseIntent(
            BassPhraseIntentKind.RELEASE,
            BassPhraseDirection.RECOVER,
            .30, .34, .42, 2,
            ("late phrase favors recovery and release",),
        )

    # Without explicit phrase position, do not invent one. Use only committed
    # local state and ensemble evidence.
    if ctx.memory.recent_complexity >= .62:
        return BassPhraseIntent(
            BassPhraseIntentKind.RELEASE,
            BassPhraseDirection.RECOVER,
            .24, .32, .40, 2,
            ("recent bass complexity creates phrase-level release debt",),
        )

    if abs(ctx.memory.phrase_register_slope) >= 2.0:
        return BassPhraseIntent(
            BassPhraseIntentKind.SUSTAIN,
            BassPhraseDirection.RECOVER,
            .36, .40, .46, 3,
            ("register excursion needs recovery before another build",),
        )

    if ctx.interaction is not None and ctx.interaction.intent in {
        BassInteractionIntent.BUILD,
        BassInteractionIntent.PROPEL,
    }:
        return BassPhraseIntent(
            BassPhraseIntentKind.BUILD,
            BassPhraseDirection.RISE,
            .58, .58, .62, 3,
            ("ensemble interaction supports a bass build",),
        )

    if ctx.interaction is not None and ctx.interaction.intent in {
        BassInteractionIntent.YIELD,
        BassInteractionIntent.HOLD,
        BassInteractionIntent.RESET,
    }:
        return BassPhraseIntent(
            BassPhraseIntentKind.GROUND,
            BassPhraseDirection.STABLE,
            .24, .30, .42, 3,
            ("ensemble interaction asks bass to simplify and ground",),
        )

    # Preserve a still-valid prior intention so every event does not cause a
    # new phrase plan.
    if (
        previous is not None
        and actions_under_previous < max(1, previous.persistence)
        and previous.kind not in {BassPhraseIntentKind.RELEASE, BassPhraseIntentKind.RESET}
    ):
        return previous

    return BassPhraseIntent(
        BassPhraseIntentKind.DEVELOP,
        BassPhraseDirection.STABLE,
        .42, .46, .50, 4,
        ("neutral context supports restrained development",),
    )
