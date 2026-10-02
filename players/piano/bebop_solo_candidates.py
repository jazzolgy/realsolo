"""Immediate bebop solo candidate generation from resolved harmonic material.

This generator creates only next-event candidates. It does not construct or store
multi-note phrases.
"""
from __future__ import annotations

from typing import Iterable

from music_intelligence.harmony.scale_linear_core import LinearConnectionAffordance
from music_intelligence.reasoning.legend_style_core import CandidateEvent

from .bebop_phrase_intent import (
    BebopEntryMode,
    BebopPhraseIntent,
    BebopTargetMode,
)
from .shared_linear_adapter import realize_shared_linear_affordances
from .voicing import ResolvedHarmonicMaterial


STRUCTURAL_ROLE_NAMES = (
    "3rd",
    "b3",
    "7th",
    "b7",
    "root",
    "5th",
    "9th",
    "9",
    "11th",
    "11",
    "13th",
    "13",
)


def _role_pitch_classes(
    material: ResolvedHarmonicMaterial,
    roles: Iterable[str],
) -> tuple[tuple[str,int],...]:
    out=[]
    for role in roles:
        for pc in material.role_pitch_classes.get(role,()):
            out.append((role,pc))
    return tuple(out)


def _nearest_pitch_for_pc(
    pc: int,
    *,
    anchor_midi: int,
    low_midi: int,
    high_midi: int,
) -> int | None:
    choices=[n for n in range(low_midi,high_midi+1) if n%12==pc]
    if not choices:
        return None
    return min(choices,key=lambda n:abs(n-anchor_midi))


def _event_key(event: CandidateEvent) -> tuple:
    return (
        event.pitch_midi,
        event.duration_beats,
        event.onset_offset_beats,
        tuple(sorted(event.tags)),
    )


def generate_immediate_bebop_candidates(
    *,
    current_material: ResolvedHarmonicMaterial,
    intent: BebopPhraseIntent,
    previous_pitch_midi: int | None = None,
    next_material: ResolvedHarmonicMaterial | None = None,
    low_midi: int = 48,
    high_midi: int = 96,
    duration_beats: float = 0.5,
    linear_affordances: tuple[LinearConnectionAffordance, ...] = (),
) -> tuple[CandidateEvent,...]:
    """Generate a bounded set of immediate melodic candidates."""
    current_material.validate()
    intent.validate()
    if next_material is not None:
        next_material.validate()
    if not 21 <= low_midi < high_midi <= 108:
        raise ValueError("invalid piano solo range")
    if duration_beats <= 0:
        raise ValueError("duration_beats must be positive")

    anchor=previous_pitch_midi if previous_pitch_midi is not None else (low_midi+high_midi)//2
    anchor=max(low_midi,min(high_midi,anchor))

    target_material=current_material
    target_prefix="current"
    if (
        intent.target_mode is BebopTargetMode.NEXT_HARMONY
        and next_material is not None
    ):
        target_material=next_material
        target_prefix="next"

    target_roles=_role_pitch_classes(target_material,STRUCTURAL_ROLE_NAMES)
    events=[]

    # When Shared Scale/Linear Intelligence is available, consume its route
    # affordances instead of independently inventing piano-local connector logic.
    shared_linear_events = ()
    if linear_affordances:
        shared_linear_events = realize_shared_linear_affordances(
            linear_affordances,
            anchor_midi=anchor,
            low_midi=low_midi,
            high_midi=high_midi,
            duration_beats=duration_beats,
            pickup=intent.entry_mode is BebopEntryMode.PICKUP,
        )
        events.extend(shared_linear_events)

    for role,pc in target_roles:
        pitch=_nearest_pitch_for_pc(
            pc,
            anchor_midi=anchor,
            low_midi=low_midi,
            high_midi=high_midi,
        )
        if pitch is None:
            continue
        tags={
            "chord_tone",
            "harmonic_identity",
            f"role:{role}",
            f"target:{target_prefix}",
        }
        if role in {"3rd","b3","7th","b7"}:
            tags.add("guide_tone")
        if intent.target_mode is BebopTargetMode.RESOLUTION:
            tags |= {"directed_target","resolution_path"}
        if intent.target_mode is BebopTargetMode.NEXT_HARMONY:
            tags |= {"anticipation","next_harmony_target"}

        onset=0.0
        if intent.entry_mode is BebopEntryMode.PICKUP:
            onset=-0.125
            tags |= {"pickup","syncopated_entry","anticipation"}

        events.append(
            CandidateEvent(
                pitch,
                duration_beats,
                onset_offset_beats=onset,
                tags=frozenset(tags),
            )
        )

        # Compatibility fallback only. Shared Core owns connector semantics when
        # linear_affordances are supplied.
        if not linear_affordances and "close_approach" in intent.connector_families:
            for offset in (-1,1):
                approach=pitch+offset
                if low_midi <= approach <= high_midi:
                    events.append(
                        CandidateEvent(
                            approach,
                            duration_beats/2,
                            onset_offset_beats=onset,
                            tags=frozenset({
                                "close_approach",
                                "connector",
                                "directed_target",
                                f"approach_to:{pitch}",
                                f"target:{target_prefix}",
                            }),
                        )
                    )

    # Neighbor/passing candidates are relative to the actually played previous note.
    if previous_pitch_midi is not None and not linear_affordances:
        if "neighbor" in intent.connector_families:
            for offset in (-2,-1,1,2):
                pitch=previous_pitch_midi+offset
                if low_midi <= pitch <= high_midi:
                    events.append(
                        CandidateEvent(
                            pitch,
                            duration_beats/2,
                            tags=frozenset({"neighbor","connector"}),
                        )
                    )
        if "passing" in intent.connector_families:
            for offset in (-1,1):
                pitch=previous_pitch_midi+offset
                if low_midi <= pitch <= high_midi:
                    events.append(
                        CandidateEvent(
                            pitch,
                            duration_beats/2,
                            tags=frozenset({"passing","connector"}),
                        )
                    )

    if intent.entry_mode is BebopEntryMode.HOLD_SPACE:
        events.append(
            CandidateEvent(
                None,
                duration_beats,
                tags=frozenset({"rest","ensemble_space"}),
            )
        )

    # Keep one rest alternative in sparse intentions, but do not force silence.
    if intent.density_direction.value in {"sparse","release"}:
        events.append(
            CandidateEvent(
                None,
                duration_beats/2,
                tags=frozenset({"rest","ensemble_space"}),
            )
        )

    # Deterministic dedupe.
    unique=[]
    seen=set()
    for event in events:
        key=_event_key(event)
        if key in seen:
            continue
        seen.add(key)
        unique.append(event)

    return tuple(unique)
