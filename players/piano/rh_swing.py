"""Right-hand swing and phrase elasticity for piano melody/solo events.

This is not a fixed 2:1 quantizer. It applies context-sensitive timing to the current
event only, preserving the one-event improvisation contract.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from music_intelligence.reasoning.legend_style_core import CandidateEvent


class SwingRole(str, Enum):
    HEAD = "head"
    SOLO = "solo"


@dataclass(frozen=True)
class RHSwingContext:
    tempo_bpm: float = 130.0
    role: SwingRole = SwingRole.SOLO
    subdivision_phase: float = 0.0  # 0.0 = beat, 0.5 = notated off-eighth
    phrase_maturity: float = 0.5
    phrase_end_pressure: float = 0.0
    anticipation_strength: float = 0.0
    triplet_context: bool = False
    confidence: float = 1.0

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


def swing_ratio_for_tempo(tempo_bpm: float) -> float:
    """Return long:short eighth ratio; faster tempos approach straighter eighths."""
    if tempo_bpm <= 90:
        return 2.05
    if tempo_bpm >= 220:
        return 1.28
    # ~1.78 at 130 bpm.
    return 2.05 - (tempo_bpm-90.0) * (0.77/130.0)


def apply_rh_swing(
    event: CandidateEvent,
    context: RHSwingContext,
) -> CandidateEvent:
    """Apply current-note swing/phrase elasticity without creating future notes."""
    context.validate()
    tags=set(event.tags)
    onset=event.onset_offset_beats
    duration=event.duration_beats

    if event.pitch_midi is None:
        return event

    ratio=swing_ratio_for_tempo(context.tempo_bpm)
    offbeat=context.subdivision_phase >= 0.40

    # Delay the second eighth toward the triplet region, but not rigidly.
    if offbeat and duration <= 0.75 and not context.triplet_context:
        target_phase=ratio/(ratio+1.0)
        delay=max(0.0,target_phase-0.5)
        onset += delay * context.confidence
        tags |= {"swing_offbeat","rh_swing"}
    else:
        tags.add("rh_swing")

    # Phrase-level elasticity inspired by observed jazz phrasing rather than
    # notation playback: anticipations can lean forward; endings can lay back.
    if context.anticipation_strength >= .55 and {"anticipation","pickup","syncopated_entry"} & tags:
        onset -= 0.035 * context.anticipation_strength * context.confidence
        tags.add("phrase_lean_forward")

    if context.phrase_end_pressure >= .6:
        onset += 0.03 * context.phrase_end_pressure * context.confidence
        duration *= 1.12
        tags.add("phrase_lay_back")

    # Head interpretation can hold structural melody tones longer than solo notes.
    if context.role is SwingRole.HEAD and (
        "guide_tone" in tags or "harmonic_identity" in tags or "melody_structural" in tags
    ):
        duration *= 1.08
        tags.add("head_phrase_elasticity")

    return replace(
        event,
        onset_offset_beats=onset,
        duration_beats=max(.0625,duration),
        tags=frozenset(tags),
    )
