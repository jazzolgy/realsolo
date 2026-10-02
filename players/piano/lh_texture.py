"""Left-hand texture classification and context-sensitive preference.

This implements piano-local realization policy. Harmony/tension availability still
comes from Shared Core-resolved material; Piano only decides how much of that material
to realize in the current LH texture.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from .ensemble_role import PianoEnsembleMode

if TYPE_CHECKING:
    from .comping import PianoCompingCandidate, PianoCompingContext


class LHTextureClass(str, Enum):
    LAY_OUT = "lay_out"
    SINGLE_STRUCTURAL = "single_structural"
    GUIDE_DYAD = "guide_dyad"
    ROOT_ANCHOR = "root_anchor"
    ONE_TENSION = "one_tension"
    TWO_TENSION = "two_tension"
    ALTERED_COLOR = "altered_color"
    SUSTAINED_COLOR = "sustained_color"
    OTHER = "other"


@dataclass(frozen=True)
class LHTextureBias:
    texture: LHTextureClass
    score_delta: float
    components: dict[str, float]
    reasons: tuple[str, ...]


def classify_lh_texture(candidate: PianoCompingCandidate) -> LHTextureClass:
    if candidate.realization is None:
        return LHTextureClass.LAY_OUT

    event=candidate.realization.event
    family=event.source_family.removeprefix("piano_")
    voices=event.voices
    roles={v.harmonic_role or "" for v in voices}
    tension_count=int(event.annotations.get("tension_count",0))

    altered_roles={"b9","#9","b13","#11"}
    if roles & altered_roles:
        return LHTextureClass.ALTERED_COLOR
    if family=="root_anchor" or (len(voices)==1 and "root" in roles):
        return LHTextureClass.ROOT_ANCHOR
    if len(voices)==1:
        return LHTextureClass.SINGLE_STRUCTURAL
    if family=="shell" and len(voices)<=2:
        return LHTextureClass.GUIDE_DYAD
    if tension_count>=2:
        return LHTextureClass.TWO_TENSION
    if tension_count==1:
        if getattr(candidate.action_type,"value",candidate.action_type) == "sustained_support":
            return LHTextureClass.SUSTAINED_COLOR
        return LHTextureClass.ONE_TENSION
    if getattr(candidate.action_type,"value",candidate.action_type) == "sustained_support" and len(voices)>=3:
        return LHTextureClass.SUSTAINED_COLOR
    return LHTextureClass.OTHER


def evaluate_lh_texture_bias(
    candidate: PianoCompingCandidate,
    context: PianoCompingContext,
) -> LHTextureBias:
    context.validate()
    texture=classify_lh_texture(candidate)
    score=0.0
    components: dict[str,float]={}
    reasons: list[str]=[]

    def add(key: str, value: float, reason: str) -> None:
        nonlocal score
        score += value
        components[key]=components.get(key,0.0)+value
        reasons.append(reason)

    trio=context.ensemble_mode in {
        PianoEnsembleMode.PIANO_HEAD_TRIO,
        PianoEnsembleMode.PIANO_SOLO_TRIO,
    }
    foreground=max(context.soloist_activity,context.piano_foreground_activity)
    busy=foreground>=0.72
    open_space=context.available_space_beats>=0.5 or context.phrase_boundary_probability>=0.6
    crowded=context.ensemble_density>=0.72

    if not trio:
        return LHTextureBias(texture,score,components,tuple(reasons))

    if texture is LHTextureClass.LAY_OUT:
        if busy or crowded:
            add("lh_texture_space",0.12,"busy foreground/ensemble supports LH lay-out")
        if context.phrase_boundary_probability>=0.72:
            add("lh_texture_boundary_release",0.05,"strong phrase boundary can release LH harmony")

    elif texture is LHTextureClass.GUIDE_DYAD:
        add("lh_guide_contrast",0.035,"guide-tone dyad is a useful thin contrast texture")
        if busy:
            add("lh_guide_busy_fit",0.055,"guide-tone dyad preserves harmonic identity under busy RH")

    elif texture is LHTextureClass.ONE_TENSION:
        add(
            "lh_one_tension_default",
            0.075*context.tension_preference,
            "one-tension rootless color is normal trio LH vocabulary",
        )
        if busy:
            add("lh_one_tension_busy_fit",0.02,"compact one-tension voicing can support active RH")

    elif texture is LHTextureClass.TWO_TENSION:
        add(
            "lh_two_tension_default",
            0.095*context.tension_preference,
            "two-tension rootless color is common when bass owns the root",
        )
        if open_space and not crowded:
            add("lh_two_tension_space",0.045,"open phrase space permits richer LH color")
        if busy and crowded:
            add("lh_two_tension_crowding",-0.045,"dense foreground plus ensemble limits rich LH texture")

    elif texture is LHTextureClass.ALTERED_COLOR:
        if open_space and not busy:
            add(
                "lh_altered_contextual",
                0.04*context.tension_preference,
                "explicit altered color can be used when the texture leaves room",
            )
        elif busy or crowded:
            add("lh_altered_restraint",-0.055,"altered color is restrained in an already dense texture")

    elif texture is LHTextureClass.ROOT_ANCHOR:
        if context.bass_activity<=0.3:
            add("lh_root_bass_space",0.055,"root anchor can clarify structure when bass leaves space")
        else:
            add("lh_root_duplication",-0.07,"active bass usually makes routine LH root doubling unnecessary")
        if context.phrase_boundary_probability>=0.72:
            add("lh_root_structural_cue",0.035,"root anchor can mark a strong structural boundary")

    elif texture is LHTextureClass.SINGLE_STRUCTURAL:
        if busy:
            add("lh_single_note_space",0.045,"single structural tone preserves space under active RH")

    elif texture is LHTextureClass.SUSTAINED_COLOR:
        if not busy and context.section_energy<=0.55:
            add("lh_sustained_color",0.05,"spacious texture can support sustained color")
        if context.section_energy>=0.75:
            add("lh_sustain_energy_restraint",-0.035,"high energy can favor more articulated LH behavior")

    return LHTextureBias(texture,score,components,tuple(reasons))
