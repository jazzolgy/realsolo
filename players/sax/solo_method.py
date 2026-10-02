"""Project Sax runtime state into Shared Solo Grammar."""
from __future__ import annotations

from music_intelligence.reasoning.solo_grammar import (
    SoloArc,
    SoloMethodContext,
    SoloMethodOption,
    shared_solo_method_options,
)


def sax_shared_solo_options(
    *,
    phrase_maturity: float,
    ensemble_activity: float,
    phrase_space_available: float = 0.0,
    form_boundary_pressure: float = 0.0,
    future_harmony_available: bool = False,
    interaction_role: str = "",
    recent_repetition_count: int = 0,
    arc: SoloArc = SoloArc.DEVELOP,
) -> tuple[SoloMethodOption, ...]:
    context = SoloMethodContext(
        phrase_maturity=phrase_maturity,
        ensemble_activity=ensemble_activity,
        phrase_space_available=phrase_space_available,
        form_boundary_pressure=form_boundary_pressure,
        future_harmony_available=future_harmony_available,
        interaction_role=interaction_role,
        recent_repetition_count=recent_repetition_count,
    )
    return shared_solo_method_options(context, arc=arc)
