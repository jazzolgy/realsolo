"""Experimental comping-role occupancy / partner coverage model.

Cross-source basis:
- Danielsson: piano/guitar conflict avoidance requires knowing roles, listening, and
  deciding which instrument is primary; when guitar supplies continuous harmonic
  material, piano can play sparsely/rhythmically/percussively.
- Dobbins: accompanist role should remain supportive rather than oppressive.

This module is piano-local for experimentation, but the representation is likely
instrument-independent and may later move to Shared Core.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class CompingPriority(str, Enum):
    UNSPECIFIED = "unspecified"
    PIANO_PRIMARY = "piano_primary"
    OTHER_PRIMARY = "other_primary"
    SHARED = "shared"


@dataclass(frozen=True)
class CompingRoleOccupancy:
    priority: CompingPriority = CompingPriority.UNSPECIFIED
    other_comping_activity: float = 0.0
    other_harmonic_coverage: float = 0.0
    other_rhythmic_coverage: float = 0.0
    harmonic_agreement_confidence: float = 1.0

    def validate(self) -> None:
        for name in (
            "other_comping_activity",
            "other_harmonic_coverage",
            "other_rhythmic_coverage",
            "harmonic_agreement_confidence",
        ):
            value=getattr(self,name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


@dataclass(frozen=True)
class RoleOccupancyBias:
    total: float
    components: Mapping[str,float]
    reasons: tuple[str,...]


def evaluate_role_occupancy_bias(candidate: Any, occupancy: CompingRoleOccupancy) -> RoleOccupancyBias:
    occupancy.validate()
    score=0.0
    components: dict[str,float]={}
    reasons:list[str]=[]

    role=getattr(getattr(candidate,"role",None),"value","")
    action=getattr(getattr(candidate,"action_type",None),"value","")
    realization=getattr(candidate,"realization",None)
    tags=set(getattr(candidate,"tags",()))
    if realization is not None:
        tags |= set(realization.event.tags)

    def add(key:str,value:float,reason:str)->None:
        nonlocal score
        score += value
        components[key]=components.get(key,0.0)+value
        reasons.append(reason)

    coverage=max(occupancy.other_comping_activity, occupancy.other_harmonic_coverage)

    if occupancy.priority is CompingPriority.OTHER_PRIMARY:
        if role=="lay_out":
            add("yield_to_primary",0.16*coverage,"other comping instrument is primary, so piano space is valuable")
        if role in {"support","punctuate"} and ("sparse" in tags or action=="sparse_support" or action=="punctuation"):
            add("secondary_sparse_fit",0.10*coverage,"sparse piano role complements a primary comping instrument")
        if role in {"build","anchor"} and coverage >= 0.6:
            add("primary_role_conflict",-0.12*coverage,"build/anchor risks competing with the primary comping instrument")
        if action=="sustained_support" and occupancy.other_harmonic_coverage >= 0.65:
            add("harmonic_coverage_conflict",-0.12*occupancy.other_harmonic_coverage,"sustained piano harmony duplicates strong external harmonic coverage")
        if "touch:percussive" in tags and occupancy.other_harmonic_coverage >= 0.6:
            add("percussive_secondary_fit",0.06*occupancy.other_harmonic_coverage,"defined piano accents can complement externally supplied harmony")

    elif occupancy.priority is CompingPriority.PIANO_PRIMARY:
        if role in {"support","anchor"}:
            add("primary_support_fit",0.08,"piano is designated primary comping support")
        if role=="lay_out" and coverage < 0.25:
            add("uncovered_support",-0.05,"laying out may leave accompaniment support uncovered")

    elif occupancy.priority is CompingPriority.SHARED:
        if coverage >= 0.65:
            if role=="lay_out":
                add("shared_space",0.08*coverage,"shared comping benefits from explicit space when partner activity is high")
            if action=="sustained_support" or "dense" in tags:
                add("shared_density_conflict",-0.10*coverage,"dense shared comping risks clutter")
            if action in {"sparse_support","punctuation"}:
                add("shared_sparse_fit",0.06*coverage,"sparse/punctuating piano gesture reduces shared comping conflict")

    if occupancy.other_rhythmic_coverage >= 0.7:
        if action=="punctuation":
            add("rhythmic_complement",0.05*occupancy.other_rhythmic_coverage,"punctuation can complement a stable external rhythmic comping layer")
        if action=="sustained_support" and occupancy.other_harmonic_coverage >= 0.6:
            add("double_coverage",-0.05,"sustained piano comping adds weight where rhythm and harmony are already covered")

    if occupancy.harmonic_agreement_confidence < 0.5 and realization is not None:
        add(
            "harmonic_disagreement_risk",
            -0.12*(1.0-occupancy.harmonic_agreement_confidence),
            "uncertain agreement between comping instruments favors caution before adding harmony",
        )

    return RoleOccupancyBias(score,components,tuple(reasons))
