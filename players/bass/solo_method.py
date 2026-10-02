"""Project Bass phrase state into Shared Solo Grammar."""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.reasoning.solo_grammar import (
    SoloArc,
    SoloDevelopmentOperation,
    SoloMethodContext,
    SoloMethodOption,
    shared_solo_method_options,
)
from .phrase_intent import BassPhraseContext, BassPhraseIntent, BassPhraseIntentKind


_KIND_TO_ARC = {
    BassPhraseIntentKind.GROUND: SoloArc.OPEN,
    BassPhraseIntentKind.DEVELOP: SoloArc.DEVELOP,
    BassPhraseIntentKind.BUILD: SoloArc.INTENSIFY,
    BassPhraseIntentKind.SUSTAIN: SoloArc.DEVELOP,
    BassPhraseIntentKind.RELEASE: SoloArc.RELEASE,
    BassPhraseIntentKind.RESET: SoloArc.REENTRY,
}


def bass_shared_solo_options(
    ctx: BassPhraseContext,
    intent: BassPhraseIntent,
    *,
    recent_repetition_count: int = 0,
    future_harmony_available: bool = False,
) -> tuple[SoloMethodOption, ...]:
    ctx.validate()
    interaction_role = ""
    if ctx.interaction is not None:
        interaction_role = ctx.interaction.intent.value.upper()

    shared = SoloMethodContext(
        phrase_maturity=(
            ctx.phrase_progress
            if ctx.phrase_progress is not None
            else (1.0 if ctx.phrase_boundary or ctx.form_boundary else 0.5)
        ),
        tension=max(0.0, min(1.0, intent.complexity_target)),
        ensemble_activity=ctx.ensemble_activity,
        recent_repetition_count=recent_repetition_count,
        phrase_space_available=max(
            0.0,
            min(1.0, 1.0 - intent.information_density_target),
        ),
        form_boundary_pressure=1.0 if ctx.form_boundary else 0.0,
        future_harmony_available=future_harmony_available,
        interaction_role=interaction_role,
    )
    return shared_solo_method_options(shared, arc=_KIND_TO_ARC[intent.kind])
