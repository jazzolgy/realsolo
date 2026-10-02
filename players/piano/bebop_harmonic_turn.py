"""Combine observed bebop turn-taking with Shared Core harmonic/form context.

Audio-derived turn-taking morphology and harmonic reasoning remain separate evidence
streams. This adapter combines them only as a current-moment policy context.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.harmony.jazz_harmony_core import HarmonicFrame, HarmonicIntent
from music_intelligence.harmony.orchestrator import HarmonicReasoningResult

from .bebop_turn_taking import BebopTurnTakingEvidence, BebopTurnTakingType


class BebopHarmonicPhase(str, Enum):
    STABLE_FIELD = "stable_field"
    DIRECTED_RESOLUTION = "directed_resolution"
    ANTICIPATORY = "anticipatory"
    FORM_BOUNDARY = "form_boundary"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class BebopHarmonicTurnContext:
    phase: BebopHarmonicPhase = BebopHarmonicPhase.AMBIGUOUS
    turn_type: BebopTurnTakingType = BebopTurnTakingType.AMBIGUOUS
    phrase_boundary_pressure: float = 0.0
    anticipation_strength: float = 0.0
    resolution_strength: float = 0.0
    stability_strength: float = 0.0
    confidence: float = 0.0

    def validate(self) -> None:
        for name in (
            "phrase_boundary_pressure",
            "anticipation_strength",
            "resolution_strength",
            "stability_strength",
            "confidence",
        ):
            value=getattr(self,name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


def _function_text(frame: HarmonicFrame) -> str:
    parts=[]
    for ev in (frame.inferred,frame.observed,frame.expected):
        if ev is not None and ev.function:
            parts.append(ev.function.lower())
    return " ".join(parts)


def derive_bebop_harmonic_turn_context(
    frame: HarmonicFrame,
    turn: BebopTurnTakingEvidence,
    reasoning: HarmonicReasoningResult | None = None,
) -> BebopHarmonicTurnContext:
    frame.validate()
    turn.validate()

    boundary=max(
        0.0,
        min(1.0,(frame.phrase_position-0.72)/0.28),
    )
    if (frame.cadence_state or "open").lower() not in {"open","none",""}:
        boundary=max(boundary,0.55)

    funcs=_function_text(frame)
    dominant=(
        "dominant" in funcs
        or funcs.strip() in {"v","v7"}
    )

    anticipation=0.0
    resolution=0.0
    stability=0.0

    if frame.next_expected is not None:
        anticipation=0.65

    if dominant:
        resolution=max(resolution,0.75)

    if reasoning is not None:
        for option in reasoning.action_options:
            strength=max(0.0,min(1.0,option.confidence*option.interpretation_compatibility))
            if option.intent is HarmonicIntent.ANTICIPATE:
                anticipation=max(anticipation,strength)
            elif option.intent in {HarmonicIntent.CONNECT,HarmonicIntent.STABILIZE}:
                resolution=max(resolution,0.75*strength)
            elif option.intent in {HarmonicIntent.COLOR,HarmonicIntent.DELAY_RESOLUTION}:
                stability=max(stability,0.65*strength)

    if not dominant and frame.tension <= 0.4:
        stability=max(stability,0.60)

    if boundary >= 0.65:
        phase=BebopHarmonicPhase.FORM_BOUNDARY
    elif anticipation >= 0.70:
        phase=BebopHarmonicPhase.ANTICIPATORY
    elif resolution >= 0.65:
        phase=BebopHarmonicPhase.DIRECTED_RESOLUTION
    elif stability >= 0.55:
        phase=BebopHarmonicPhase.STABLE_FIELD
    else:
        phase=BebopHarmonicPhase.AMBIGUOUS

    confidence=min(
        1.0,
        0.45*turn.confidence
        + 0.20*boundary
        + 0.15*anticipation
        + 0.15*resolution
        + 0.05*stability,
    )

    result=BebopHarmonicTurnContext(
        phase=phase,
        turn_type=turn.episode_type,
        phrase_boundary_pressure=boundary,
        anticipation_strength=anticipation,
        resolution_strength=resolution,
        stability_strength=stability,
        confidence=confidence,
    )
    result.validate()
    return result
