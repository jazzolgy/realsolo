"""Piano-side compatibility helpers for the Shared GrooveTemporalContext.

Shared Core owns the ensemble pulse and swing ratio. Piano only realizes that
shared timing and may add small phrase-local elasticity for the current event.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from music_intelligence.reasoning.groove_context import (
    GrooveFeel,
    GrooveTemporalContext,
    build_groove_context,
    groove_timing_offset_beats,
)
from music_intelligence.reasoning.legend_style_core import CandidateEvent


class SwingRole(str, Enum):
    HEAD = "head"
    SOLO = "solo"


@dataclass(frozen=True)
class RHSwingContext:
    tempo_bpm: float = 130.0
    role: SwingRole = SwingRole.SOLO
    subdivision_phase: float = 0.0
    phrase_maturity: float = 0.5
    phrase_end_pressure: float = 0.0
    anticipation_strength: float = 0.0
    triplet_context: bool = False
    confidence: float = 1.0
    groove: GrooveTemporalContext | None = None

    def validate(self) -> None:
        if not 40 <= self.tempo_bpm <= 360:
            raise ValueError("tempo_bpm outside supported range")
        for name in (
            "subdivision_phase",
            "phrase_maturity",
            "phrase_end_pressure",
            "anticipation_strength",
            "confidence",
        ):
            value=getattr(self,name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.groove is not None:
            self.groove.validate()


def _shared_swing_context(context: RHSwingContext) -> GrooveTemporalContext:
    if context.groove is not None:
        return context.groove
    return build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=context.tempo_bpm,
        groove_strength=context.confidence,
        provenance=("piano_rh_swing_compat","shared_groove_default"),
    )


def swing_ratio_for_tempo(tempo_bpm: float) -> float:
    """Compatibility accessor; the ratio itself is owned by Shared Core."""
    return build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=tempo_bpm,
    ).effective_swing_ratio


def apply_rh_swing(
    event: CandidateEvent,
    context: RHSwingContext,
) -> CandidateEvent:
    """Realize shared swing plus small current-phrase elasticity.

    Solo runtime should normally receive groove timing in PianoSoloRealizer.
    This helper remains useful for written-head realization and compatibility.
    """
    context.validate()
    if event.pitch_midi is None:
        return event

    tags=set(event.tags)
    onset=event.onset_offset_beats
    duration=event.duration_beats
    groove=_shared_swing_context(context)

    if not context.triplet_context:
        onset += groove_timing_offset_beats(
            context.subdivision_phase,
            groove,
            swing_eligible=True,
        )
        if abs(context.subdivision_phase-.5) <= .08:
            tags.add("swing_offbeat")
    tags |= {"rh_swing",f"groove:{groove.feel.value}"}

    if (
        context.anticipation_strength >= .55
        and {"anticipation","pickup","syncopated_entry"} & tags
    ):
        onset -= .035 * context.anticipation_strength * context.confidence
        tags.add("phrase_lean_forward")

    if context.phrase_end_pressure >= .6:
        onset += .03 * context.phrase_end_pressure * context.confidence
        duration *= 1.12
        tags.add("phrase_lay_back")

    if context.role is SwingRole.HEAD and (
        "guide_tone" in tags
        or "harmonic_identity" in tags
        or "melody_structural" in tags
    ):
        duration *= 1.08
        tags.add("head_phrase_elasticity")

    return replace(
        event,
        onset_offset_beats=onset,
        duration_beats=max(.0625,duration),
        tags=frozenset(tags),
    )
