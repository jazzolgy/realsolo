"""Experimental register / dynamics / touch realization grammar.

Source-derived motivation: McNeely repeatedly varies register, voicing weight,
dynamics, sustain, and articulation as comping develops. The exact mappings below
are RealSolo heuristics, not claims that the source prescribes these categories.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .comping import InteractionRole, PianoCompingCandidate
from .interaction import EnergyDirection, PianoInteractionState


class RegisterDirection(str, Enum):
    LOWER = "lower"
    STAY = "stay"
    HIGHER = "higher"


class DynamicLevel(str, Enum):
    SOFT = "soft"
    MEDIUM = "medium"
    STRONG = "strong"


class TouchType(str, Enum):
    NEUTRAL = "neutral"
    LEGATO = "legato"
    PERCUSSIVE = "percussive"


@dataclass(frozen=True)
class PianoExpressionIntent:
    register_direction: RegisterDirection = RegisterDirection.STAY
    dynamic_level: DynamicLevel = DynamicLevel.MEDIUM
    touch: TouchType = TouchType.NEUTRAL
    confidence: float = 1.0
    source: str = "piano_expression_grammar"

    def validate(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


def expression_intents_for_candidate(
    candidate: PianoCompingCandidate,
    interaction: PianoInteractionState,
    *,
    bass_activity: float = 0.5,
    soloist_register_midi: float | None = None,
) -> tuple[PianoExpressionIntent, ...]:
    """Expose plural immediate expression alternatives.

    This returns options only for the current gesture and does not schedule a
    register/dynamic trajectory into the future.
    """
    candidate.validate()
    interaction.validate()
    if not 0.0 <= bass_activity <= 1.0:
        raise ValueError("bass_activity must be within 0..1")
    if soloist_register_midi is not None and not 0 <= soloist_register_midi <= 127:
        raise ValueError("soloist_register_midi must be within MIDI range")

    if candidate.realization is None:
        return ()

    role = candidate.role
    out: list[PianoExpressionIntent] = [
        PianoExpressionIntent(
            RegisterDirection.STAY,
            DynamicLevel.MEDIUM,
            TouchType.NEUTRAL,
            confidence=0.82,
        )
    ]

    if interaction.energy_direction is EnergyDirection.UP:
        out.append(
            PianoExpressionIntent(
                RegisterDirection.HIGHER,
                DynamicLevel.STRONG,
                TouchType.PERCUSSIVE
                if role in {InteractionRole.PUNCTUATE, InteractionRole.ANCHOR, InteractionRole.BUILD}
                else TouchType.NEUTRAL,
                confidence=0.76,
            )
        )

    if interaction.energy_direction is EnergyDirection.DOWN:
        out.append(
            PianoExpressionIntent(
                RegisterDirection.STAY,
                DynamicLevel.SOFT,
                TouchType.LEGATO
                if role in {InteractionRole.SUPPORT, InteractionRole.RELEASE}
                else TouchType.NEUTRAL,
                confidence=0.78,
            )
        )

    if bass_activity >= 0.7:
        out.append(
            PianoExpressionIntent(
                RegisterDirection.HIGHER,
                DynamicLevel.SOFT
                if interaction.ensemble_density >= 0.65
                else DynamicLevel.MEDIUM,
                TouchType.NEUTRAL,
                confidence=0.74,
            )
        )
    elif bass_activity <= 0.3 and role in {InteractionRole.ANCHOR, InteractionRole.SUPPORT}:
        out.append(
            PianoExpressionIntent(
                RegisterDirection.LOWER,
                DynamicLevel.MEDIUM,
                TouchType.NEUTRAL,
                confidence=0.62,
            )
        )

    if soloist_register_midi is not None:
        event_center = sum(candidate.realization.event.pitches_midi) / len(
            candidate.realization.event.pitches_midi
        )
        if abs(event_center - soloist_register_midi) < 7:
            out.append(
                PianoExpressionIntent(
                    RegisterDirection.LOWER
                    if event_center > 60
                    else RegisterDirection.HIGHER,
                    DynamicLevel.SOFT,
                    TouchType.NEUTRAL,
                    confidence=0.70,
                )
            )

    # Deduplicate semantically identical alternatives.
    seen: set[tuple[str, str, str]] = set()
    unique: list[PianoExpressionIntent] = []
    for intent in out:
        key = (
            intent.register_direction.value,
            intent.dynamic_level.value,
            intent.touch.value,
        )
        if key not in seen:
            seen.add(key)
            unique.append(intent)
    return tuple(unique)


def _shift_octave_to_fit(pitch: int, shift: int, low: int = 21, high: int = 108) -> int:
    target = pitch + shift
    while target < low:
        target += 12
    while target > high:
        target -= 12
    return target


def apply_expression_intent(
    candidate: PianoCompingCandidate,
    intent: PianoExpressionIntent,
) -> PianoCompingCandidate:
    """Realize one register/dynamic/touch option without changing pitch classes."""
    candidate.validate()
    intent.validate()
    if candidate.realization is None:
        raise ValueError("cannot apply sounding expression intent to silence")

    realization = candidate.realization
    event = realization.event

    shift = 0
    if intent.register_direction is RegisterDirection.HIGHER:
        shift = 12
    elif intent.register_direction is RegisterDirection.LOWER:
        shift = -12

    velocity = {
        DynamicLevel.SOFT: 52,
        DynamicLevel.MEDIUM: 72,
        DynamicLevel.STRONG: 92,
    }[intent.dynamic_level]

    new_voices = tuple(
        replace(
            voice,
            pitch_midi=_shift_octave_to_fit(voice.pitch_midi, shift),
            velocity=velocity,
        )
        for voice in event.voices
    )
    new_event = replace(
        event,
        voices=new_voices,
        velocity=velocity,
        annotations={
            **dict(event.annotations),
            "register_direction": intent.register_direction.value,
            "dynamic_level": intent.dynamic_level.value,
            "touch": intent.touch.value,
        },
    )

    new_hands = tuple(
        (voice_id, hand)
        for voice_id, hand in realization.hand_assignment
    )
    new_realization = replace(
        realization,
        event=new_event,
        hand_assignment=new_hands,
        touch=intent.touch.value,
    )
    return replace(
        candidate,
        realization=new_realization,
        tags=frozenset(
            set(candidate.tags)
            | {
                f"register:{intent.register_direction.value}",
                f"dynamic:{intent.dynamic_level.value}",
                f"touch:{intent.touch.value}",
            }
        ),
    )


def expand_expression_variants(
    candidate: PianoCompingCandidate,
    interaction: PianoInteractionState,
    *,
    bass_activity: float = 0.5,
    soloist_register_midi: float | None = None,
) -> tuple[PianoCompingCandidate, ...]:
    intents = expression_intents_for_candidate(
        candidate,
        interaction,
        bass_activity=bass_activity,
        soloist_register_midi=soloist_register_midi,
    )
    return tuple(apply_expression_intent(candidate, x) for x in intents)
