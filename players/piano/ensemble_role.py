"""Piano ensemble-role and hand-role intelligence.

A piano is not always "the accompanist". In a piano-bass-drums trio it may be the
only melodic/harmonic foreground instrument, so head and piano-solo sections require
foreground melody/solo plus accompaniment coordination inside one instrument.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PianoEnsembleMode(str, Enum):
    EXTERNAL_MELODY_SUPPORT = "external_melody_support"
    PIANO_HEAD_TRIO = "piano_head_trio"
    PIANO_SOLO_TRIO = "piano_solo_trio"
    BASS_SOLO_SUPPORT = "bass_solo_support"
    DRUM_SOLO_DIALOGUE = "drum_solo_dialogue"
    COLLECTIVE_INTERPLAY = "collective_interplay"


class PianoHandFunction(str, Enum):
    MELODY = "melody"
    IMPROVISED_SOLO = "improvised_solo"
    COMPING = "comping"
    TWO_HAND_COMPING = "two_hand_comping"
    DIALOGUE = "dialogue"
    CUE = "cue"
    LAY_OUT = "lay_out"


@dataclass(frozen=True)
class PianoEnsembleRoleContext:
    """Current ensemble ownership, not a permanent instrument identity."""

    section_role: str = "unknown"
    external_melody_active: bool = False
    piano_is_only_melodic_instrument: bool = False
    bass_solo_active: bool = False
    drum_solo_active: bool = False
    collective_interplay: bool = False


@dataclass(frozen=True)
class PianoHandRolePlan:
    mode: PianoEnsembleMode
    right_hand: PianoHandFunction
    left_hand: PianoHandFunction
    piano_owns_foreground: bool
    left_hand_comping_is_optional: bool = True
    allow_two_hand_texture: bool = False

    def validate(self) -> None:
        if self.piano_owns_foreground and self.mode in {
            PianoEnsembleMode.PIANO_HEAD_TRIO,
            PianoEnsembleMode.PIANO_SOLO_TRIO,
        }:
            if self.left_hand is not PianoHandFunction.COMPING:
                raise ValueError("foreground trio piano requires coordinated LH comping role")


def derive_piano_hand_role_plan(
    context: PianoEnsembleRoleContext,
) -> PianoHandRolePlan:
    """Resolve current piano hand roles from ensemble/section ownership."""

    role=context.section_role.strip().lower().replace(" ","_")

    if context.bass_solo_active or role in {"bass_solo","bass_feature"}:
        plan=PianoHandRolePlan(
            PianoEnsembleMode.BASS_SOLO_SUPPORT,
            PianoHandFunction.DIALOGUE,
            PianoHandFunction.COMPING,
            piano_owns_foreground=False,
            left_hand_comping_is_optional=True,
            allow_two_hand_texture=True,
        )
    elif context.drum_solo_active or role in {"drum_solo","drums_solo","drum_feature"}:
        plan=PianoHandRolePlan(
            PianoEnsembleMode.DRUM_SOLO_DIALOGUE,
            PianoHandFunction.DIALOGUE,
            PianoHandFunction.CUE,
            piano_owns_foreground=False,
            left_hand_comping_is_optional=True,
            allow_two_hand_texture=True,
        )
    elif context.collective_interplay:
        plan=PianoHandRolePlan(
            PianoEnsembleMode.COLLECTIVE_INTERPLAY,
            PianoHandFunction.DIALOGUE,
            PianoHandFunction.COMPING,
            piano_owns_foreground=False,
            left_hand_comping_is_optional=True,
            allow_two_hand_texture=True,
        )
    elif context.piano_is_only_melodic_instrument and not context.external_melody_active:
        if role in {"head","melody","theme","head_in","head_out"}:
            plan=PianoHandRolePlan(
                PianoEnsembleMode.PIANO_HEAD_TRIO,
                PianoHandFunction.MELODY,
                PianoHandFunction.COMPING,
                piano_owns_foreground=True,
                left_hand_comping_is_optional=True,
                allow_two_hand_texture=True,
            )
        else:
            plan=PianoHandRolePlan(
                PianoEnsembleMode.PIANO_SOLO_TRIO,
                PianoHandFunction.IMPROVISED_SOLO,
                PianoHandFunction.COMPING,
                piano_owns_foreground=True,
                left_hand_comping_is_optional=True,
                allow_two_hand_texture=False,
            )
    else:
        plan=PianoHandRolePlan(
            PianoEnsembleMode.EXTERNAL_MELODY_SUPPORT,
            PianoHandFunction.TWO_HAND_COMPING,
            PianoHandFunction.TWO_HAND_COMPING,
            piano_owns_foreground=False,
            left_hand_comping_is_optional=True,
            allow_two_hand_texture=True,
        )

    plan.validate()
    return plan
