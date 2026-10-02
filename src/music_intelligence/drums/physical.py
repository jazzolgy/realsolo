"""Drum-set physical feasibility and four-limb solo orchestration."""
from __future__ import annotations

from dataclasses import dataclass

from .model import DrumGesture, DrumHit, DrumVoice, GestureRole, Limb


@dataclass(frozen=True)
class LimbCapability:
    limb: Limb
    allowed_voices: frozenset[DrumVoice]


DEFAULT_LIMB_CAPABILITIES: tuple[LimbCapability, ...] = (
    LimbCapability(
        Limb.RIGHT_HAND,
        frozenset({
            DrumVoice.RIDE, DrumVoice.CRASH, DrumVoice.SNARE,
            DrumVoice.HIGH_TOM, DrumVoice.MID_TOM, DrumVoice.FLOOR_TOM,
            DrumVoice.COWBELL, DrumVoice.CLAVE,
        }),
    ),
    LimbCapability(
        Limb.LEFT_HAND,
        frozenset({
            DrumVoice.SNARE, DrumVoice.HIGH_TOM, DrumVoice.MID_TOM,
            DrumVoice.FLOOR_TOM, DrumVoice.COWBELL, DrumVoice.CLAVE,
        }),
    ),
    LimbCapability(
        Limb.RIGHT_FOOT,
        frozenset({DrumVoice.BASS_DRUM}),
    ),
    LimbCapability(
        Limb.LEFT_FOOT,
        frozenset({DrumVoice.CLOSED_HIHAT, DrumVoice.OPEN_HIHAT}),
    ),
)


_CAPABILITY = {c.limb: c.allowed_voices for c in DEFAULT_LIMB_CAPABILITIES}


def limb_can_play(limb: Limb, voice: DrumVoice) -> bool:
    return voice in _CAPABILITY.get(limb, frozenset())


def validate_kit_reachability(gesture: DrumGesture) -> None:
    gesture.validate()
    for hit in gesture.hits:
        if not limb_can_play(hit.limb, hit.voice):
            raise ValueError(f"{hit.limb.value} cannot realize {hit.voice.value} in default kit model")


def four_limb_solo_gesture(
    *,
    right_hand: DrumVoice | None = None,
    left_hand: DrumVoice | None = None,
    right_foot: bool = False,
    left_foot_hihat: bool = False,
    velocity: int = 82,
    articulation: str = "solo_orchestration",
) -> DrumGesture:
    """Build one simultaneous four-limb solo gesture subject to feasibility."""
    hits: list[DrumHit] = []
    if right_hand is not None:
        hits.append(DrumHit(right_hand, Limb.RIGHT_HAND, velocity, articulation=articulation))
    if left_hand is not None:
        hits.append(DrumHit(left_hand, Limb.LEFT_HAND, velocity, articulation=articulation))
    if right_foot:
        hits.append(DrumHit(DrumVoice.BASS_DRUM, Limb.RIGHT_FOOT, velocity, articulation=articulation))
    if left_foot_hihat:
        hits.append(DrumHit(DrumVoice.CLOSED_HIHAT, Limb.LEFT_FOOT, max(35, velocity - 20), articulation="chick"))

    gesture = DrumGesture(
        hits=tuple(hits),
        role=GestureRole.FILL,
        tags=frozenset({"drum_solo", "four_limb", "physical_feasibility"}),
        provenance=("drum_player", "physical_model"),
    )
    validate_kit_reachability(gesture)
    return gesture
