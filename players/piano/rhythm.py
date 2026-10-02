"""Contextual rhythmic placement grammar for jazz-piano comping.

Comping rhythm must stay conversational rather than collapse into a single repeated
on-beat pattern. This module exposes plural one-gesture timing choices; it never
precomposes a future comping sequence.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .comping import CompingActionType, InteractionRole, PianoCompingCandidate


class RhythmicPlacement(str, Enum):
    ON_BEAT = "on_beat"
    ANTICIPATED = "anticipated"
    OFFBEAT = "offbeat"
    DELAYED = "delayed"
    SUSTAINED = "sustained"


@dataclass(frozen=True)
class PianoRhythmicIntent:
    placement: RhythmicPlacement
    onset_offset_beats: float = 0.0
    duration_scale: float = 1.0
    confidence: float = 1.0
    cell_id: str = ""
    source: str = "piano_rhythm_grammar"

    def validate(self) -> None:
        if self.duration_scale <= 0:
            raise ValueError("duration_scale must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        if abs(self.onset_offset_beats) > 1.0:
            raise ValueError("onset_offset_beats outside immediate-gesture range")


def _intent(
    placement: RhythmicPlacement,
    onset: float,
    duration: float,
    confidence: float,
    cell_id: str,
) -> PianoRhythmicIntent:
    return PianoRhythmicIntent(
        placement=placement,
        onset_offset_beats=onset,
        duration_scale=duration,
        confidence=confidence,
        cell_id=cell_id,
    )


def rhythmic_intents_for_candidate(
    candidate: PianoCompingCandidate,
    *,
    phrase_boundary_probability: float,
    available_space_beats: float,
    drummer_activity: float,
) -> tuple[PianoRhythmicIntent, ...]:
    """Expose varied immediate placements for one current comping gesture."""
    if not 0.0 <= phrase_boundary_probability <= 1.0:
        raise ValueError("phrase_boundary_probability must be within 0..1")
    if available_space_beats < 0:
        raise ValueError("available_space_beats cannot be negative")
    if not 0.0 <= drummer_activity <= 1.0:
        raise ValueError("drummer_activity must be within 0..1")
    if candidate.action_type is CompingActionType.SILENCE:
        return ()

    active_drums = drummer_activity >= 0.5
    phrase_open = phrase_boundary_probability >= 0.55 and available_space_beats >= 0.5

    # On-beat is now only one option, not the privileged default solution.
    out: list[PianoRhythmicIntent] = [
        _intent(RhythmicPlacement.ON_BEAT, 0.0, 0.75, 0.56, "beat_short"),
        _intent(RhythmicPlacement.ON_BEAT, 0.0, 1.20, 0.48, "beat_long"),
    ]

    # General support must have real rhythmic vocabulary; previously it had
    # effectively only ON_BEAT and therefore converged to mechanical regularity.
    if candidate.role in {
        InteractionRole.SUPPORT,
        InteractionRole.ANCHOR,
        InteractionRole.PUNCTUATE,
        InteractionRole.BUILD,
        InteractionRole.RELEASE,
    }:
        out.extend((
            _intent(
                RhythmicPlacement.ANTICIPATED, -0.5, 0.55,
                0.62 if active_drums else 0.52, "anticipate_eighth",
            ),
            _intent(
                RhythmicPlacement.ANTICIPATED, -0.125, 0.68,
                0.68 if active_drums else 0.54, "anticipate_small",
            ),
            _intent(
                RhythmicPlacement.OFFBEAT, 0.5, 0.50,
                0.64 if active_drums else 0.52, "offbeat_eighth",
            ),
            _intent(
                RhythmicPlacement.OFFBEAT, 0.125, 0.58,
                0.60 if active_drums else 0.50, "offbeat_small",
            ),
            _intent(
                RhythmicPlacement.DELAYED, 0.25, 0.70,
                0.58, "delayed_quarter",
            ),
        ))

    if candidate.role in {InteractionRole.ANSWER, InteractionRole.FILL} and phrase_open:
        out.extend((
            _intent(
                RhythmicPlacement.DELAYED, 0.25,
                min(1.3, max(0.55, available_space_beats)),
                min(1.0, phrase_boundary_probability),
                "answer_delayed",
            ),
            _intent(
                RhythmicPlacement.OFFBEAT, 0.5,
                min(1.0, max(0.45, available_space_beats * 0.75)),
                min(0.95, phrase_boundary_probability),
                "answer_offbeat",
            ),
        ))

    if candidate.action_type is CompingActionType.SUSTAINED_SUPPORT:
        out.append(
            _intent(
                RhythmicPlacement.SUSTAINED,
                0.0,
                1.7,
                0.68 if not phrase_open else 0.54,
                "sustain_open",
            )
        )

    # Deterministic de-duplication by actual timing identity.
    unique: list[PianoRhythmicIntent] = []
    seen = set()
    for item in out:
        key=(item.placement,item.onset_offset_beats,item.duration_scale,item.cell_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return tuple(unique)


def apply_rhythmic_intent(
    candidate: PianoCompingCandidate,
    intent: PianoRhythmicIntent,
) -> PianoCompingCandidate:
    intent.validate()
    candidate.validate()
    if candidate.realization is None:
        raise ValueError("cannot apply sounding rhythmic intent to silence")

    old_event = candidate.realization.event
    new_duration = max(0.0625, candidate.duration_beats * intent.duration_scale)
    new_event = replace(
        old_event,
        duration_beats=new_duration,
        onset_offset_beats=old_event.onset_offset_beats + intent.onset_offset_beats,
        annotations={
            **dict(old_event.annotations),
            "rhythmic_placement": intent.placement.value,
            "rhythm_cell": intent.cell_id,
            "rhythmic_intent_confidence": intent.confidence,
        },
    )
    new_realization = replace(candidate.realization, event=new_event)
    tags=set(candidate.tags)
    tags.add(f"rhythm:{intent.placement.value}")
    if intent.cell_id:
        tags.add(f"rhythm_cell:{intent.cell_id}")
    return replace(
        candidate,
        duration_beats=new_duration,
        realization=new_realization,
        tags=frozenset(tags),
    )


def expand_rhythmic_variants(
    candidate: PianoCompingCandidate,
    *,
    phrase_boundary_probability: float,
    available_space_beats: float,
    drummer_activity: float,
) -> tuple[PianoCompingCandidate, ...]:
    intents = rhythmic_intents_for_candidate(
        candidate,
        phrase_boundary_probability=phrase_boundary_probability,
        available_space_beats=available_space_beats,
        drummer_activity=drummer_activity,
    )
    return tuple(apply_rhythmic_intent(candidate, intent) for intent in intents)
