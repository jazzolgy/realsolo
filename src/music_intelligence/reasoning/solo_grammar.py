"""Instrument-neutral online solo methodology.

These operations are shared improvisation grammar. They are not owned by
Charlie Parker, Bill Evans, drums, piano, sax, bass, or any other source
instrument/legend.

Legends and source studies provide conditional priors and vocabulary evidence
for how/when these operations are used. Players realize them according to their
instrument grammar and physical constraints.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SoloDevelopmentOperation(str, Enum):
    STATE = "state"
    REPEAT = "repeat"
    VARY = "vary"
    FRAGMENT = "fragment"
    EXTEND = "extend"
    CONTRACT = "contract"
    INVERT = "invert"
    SEQUENCE = "sequence"
    DISPLACE = "displace"
    AUGMENT = "augment"
    DIMINISH = "diminish"
    REORCHESTRATE = "reorchestrate"
    CHANGE_REGISTER = "change_register"
    ADD_SPACE = "add_space"
    INTERNAL_REST = "internal_rest"
    CONTRAST = "contrast"
    RECAP = "recap"
    RESOLVE = "resolve"
    TARGET_NEXT_HARMONY = "target_next_harmony"
    ANSWER = "answer"


class SoloArc(str, Enum):
    OPEN = "open"
    DEVELOP = "develop"
    INTENSIFY = "intensify"
    CLIMAX = "climax"
    RELEASE = "release"
    REENTRY = "reentry"


@dataclass(frozen=True)
class SoloMethodContext:
    """Shared context for choosing the next development operation.

    This is intentionally abstract and contains no source-instrument mechanics.
    """

    phrase_maturity: float = 0.0
    tension: float = 0.0
    ensemble_activity: float = 0.5
    recent_repetition_count: int = 0
    phrase_space_available: float = 0.0
    form_boundary_pressure: float = 0.0
    future_harmony_available: bool = False
    interaction_role: str = ""

    def validate(self) -> None:
        for name in (
            "phrase_maturity",
            "tension",
            "ensemble_activity",
            "phrase_space_available",
            "form_boundary_pressure",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.recent_repetition_count < 0:
            raise ValueError("recent_repetition_count may not be negative")


@dataclass(frozen=True)
class SoloMethodOption:
    operation: SoloDevelopmentOperation
    weight: float
    reasons: tuple[str, ...] = ()


def shared_solo_method_options(
    context: SoloMethodContext,
    *,
    arc: SoloArc = SoloArc.DEVELOP,
) -> tuple[SoloMethodOption, ...]:
    """Return instrument-neutral development alternatives for the next event.

    These are soft methodology options, not future phrases.
    """

    context.validate()
    options: list[SoloMethodOption] = [
        SoloMethodOption(SoloDevelopmentOperation.STATE, 0.15, ("preserve current idea",)),
        SoloMethodOption(SoloDevelopmentOperation.VARY, 0.25, ("develop current material",)),
        SoloMethodOption(SoloDevelopmentOperation.FRAGMENT, 0.18, ("reuse partial memory",)),
    ]

    repeat_weight = 0.28 - min(0.30, 0.10 * context.recent_repetition_count)
    options.append(
        SoloMethodOption(
            SoloDevelopmentOperation.REPEAT,
            repeat_weight,
            ("repetition supports identity but is pressure-limited",),
        )
    )

    if context.phrase_space_available >= 0.45 or context.ensemble_activity >= 0.7:
        options.append(
            SoloMethodOption(
                SoloDevelopmentOperation.ADD_SPACE,
                0.24 + 0.18 * context.phrase_space_available,
                ("space is an active solo-development choice",),
            )
        )

    if context.future_harmony_available:
        options.append(
            SoloMethodOption(
                SoloDevelopmentOperation.TARGET_NEXT_HARMONY,
                0.32,
                ("future harmony may shape the next event without precomposing notes",),
            )
        )

    if context.interaction_role.upper() == "ANSWER":
        options.append(
            SoloMethodOption(
                SoloDevelopmentOperation.ANSWER,
                0.34,
                ("current ensemble role requests a response",),
            )
        )

    if arc in {SoloArc.DEVELOP, SoloArc.INTENSIFY}:
        options.extend((
            SoloMethodOption(SoloDevelopmentOperation.SEQUENCE, 0.20, ("develop arc",)),
            SoloMethodOption(SoloDevelopmentOperation.DISPLACE, 0.20, ("develop rhythmic placement",)),
            SoloMethodOption(SoloDevelopmentOperation.CHANGE_REGISTER, 0.15, ("develop register trajectory",)),
        ))

    if arc is SoloArc.INTENSIFY:
        options.extend((
            SoloMethodOption(SoloDevelopmentOperation.EXTEND, 0.24, ("increase continuity",)),
            SoloMethodOption(SoloDevelopmentOperation.DIMINISH, 0.18, ("increase event density",)),
        ))

    if arc in {SoloArc.RELEASE, SoloArc.REENTRY} or context.form_boundary_pressure >= 0.7:
        options.extend((
            SoloMethodOption(SoloDevelopmentOperation.RECAP, 0.28, ("recover identity near boundary",)),
            SoloMethodOption(SoloDevelopmentOperation.RESOLVE, 0.34, ("close or hand off current arc",)),
            SoloMethodOption(SoloDevelopmentOperation.ADD_SPACE, 0.30, ("release may remain unfilled",)),
        ))

    return tuple(options)
