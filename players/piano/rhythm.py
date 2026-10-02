"""Experimental rhythmic placement grammar for jazz-piano comping.

Source basis: McNeely repeatedly varies rhythmic placement, anticipation, duration,
offbeat activity, and phrase-response timing while holding harmonic material stable.

These are candidate descriptors for one immediate gesture, not multi-bar patterns.
"""
from __future__ import annotations

from dataclasses import dataclass
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
    source: str = "piano_rhythm_grammar"

    def validate(self) -> None:
        if self.duration_scale <= 0:
            raise ValueError("duration_scale must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        if abs(self.onset_offset_beats) > 1.0:
            raise ValueError("onset_offset_beats outside immediate-gesture range")


def rhythmic_intents_for_candidate(
    candidate: PianoCompingCandidate,
    *,
    phrase_boundary_probability: float,
    available_space_beats: float,
    drummer_activity: float,
) -> tuple[PianoRhythmicIntent, ...]:
    """Return plural immediate-placement options for the current candidate.

    This does not choose a placement. It only exposes contextually plausible timing
    alternatives to a later evaluator.
    """
    if not 0.0 <= phrase_boundary_probability <= 1.0:
        raise ValueError("phrase_boundary_probability must be within 0..1")
    if available_space_beats < 0:
        raise ValueError("available_space_beats cannot be negative")
    if not 0.0 <= drummer_activity <= 1.0:
        raise ValueError("drummer_activity must be within 0..1")

    if candidate.action_type is CompingActionType.SILENCE:
        return ()

    out: list[PianoRhythmicIntent] = [
        PianoRhythmicIntent(RhythmicPlacement.ON_BEAT, 0.0, 1.0, 0.8),
    ]

    if candidate.role in {InteractionRole.PUNCTUATE, InteractionRole.ANCHOR}:
        out.append(
            PianoRhythmicIntent(
                RhythmicPlacement.ANTICIPATED,
                onset_offset_beats=-0.125,
                duration_scale=0.65,
                confidence=0.72 if drummer_activity >= 0.5 else 0.58,
            )
        )
        out.append(
            PianoRhythmicIntent(
                RhythmicPlacement.OFFBEAT,
                onset_offset_beats=0.125,
                duration_scale=0.55,
                confidence=0.70 if drummer_activity >= 0.5 else 0.55,
            )
        )

    if (
        candidate.role in {InteractionRole.ANSWER, InteractionRole.FILL}
        and phrase_boundary_probability >= 0.55
        and available_space_beats >= 0.5
    ):
        out.append(
            PianoRhythmicIntent(
                RhythmicPlacement.DELAYED,
                onset_offset_beats=0.25,
                duration_scale=min(1.5, max(0.5, available_space_beats)),
                confidence=min(1.0, phrase_boundary_probability),
            )
        )

    if candidate.action_type is CompingActionType.SUSTAINED_SUPPORT:
        out.append(
            PianoRhythmicIntent(
                RhythmicPlacement.SUSTAINED,
                onset_offset_beats=0.0,
                duration_scale=1.6,
                confidence=0.82,
            )
        )

    return tuple(out)


from dataclasses import replace


def apply_rhythmic_intent(
    candidate: PianoCompingCandidate,
    intent: PianoRhythmicIntent,
) -> PianoCompingCandidate:
    """Apply one immediate rhythmic interpretation without changing pitch content."""
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
        },
    )
    new_realization = replace(candidate.realization, event=new_event)
    return replace(
        candidate,
        duration_beats=new_duration,
        realization=new_realization,
        tags=frozenset(set(candidate.tags) | {f"rhythm:{intent.placement.value}"}),
    )


def expand_rhythmic_variants(
    candidate: PianoCompingCandidate,
    *,
    phrase_boundary_probability: float,
    available_space_beats: float,
    drummer_activity: float,
) -> tuple[PianoCompingCandidate, ...]:
    """Expand one sounding candidate into plural immediate timing variants."""
    intents = rhythmic_intents_for_candidate(
        candidate,
        phrase_boundary_probability=phrase_boundary_probability,
        available_space_beats=available_space_beats,
        drummer_activity=drummer_activity,
    )
    return tuple(apply_rhythmic_intent(candidate, intent) for intent in intents)
