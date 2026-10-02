"""Harmonic/form-aware bebop comping bias for observed turn-taking episodes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .bebop_harmonic_turn import BebopHarmonicPhase, BebopHarmonicTurnContext
from .bebop_turn_taking import BebopTurnTakingType


@dataclass(frozen=True)
class BebopHarmonicTurnCompingBias:
    total: float
    components: Mapping[str,float]
    reasons: tuple[str,...]


def evaluate_bebop_harmonic_turn_comping_bias(candidate, context):
    context.validate()
    score=0.0
    components={}
    reasons=[]

    role=getattr(getattr(candidate,"role",None),"value","")
    action=getattr(getattr(candidate,"action_type",None),"value","")
    tags=set(getattr(candidate,"tags",()))
    realization=getattr(candidate,"realization",None)
    if realization is not None:
        tags |= set(realization.event.tags)

    weight=context.confidence

    def add(key,value,reason):
        nonlocal score
        score += value
        components[key]=components.get(key,0.0)+value
        reasons.append(reason)

    if context.phase is BebopHarmonicPhase.FORM_BOUNDARY:
        if role=="lay_out":
            add(
                "boundary_space",
                0.08*weight*max(context.phrase_boundary_pressure,0.5),
                "form boundary can preserve ensemble release",
            )
        if action=="sustained_support":
            add(
                "boundary_overfill",
                -0.05*weight,
                "sustained comping can blur a form-boundary reset",
            )
        if action=="punctuation":
            add(
                "boundary_punctuation",
                0.04*weight,
                "brief punctuation can mark the boundary without occupying it",
            )

    elif context.phase is BebopHarmonicPhase.DIRECTED_RESOLUTION:
        if {"guide_tone","voice_leading","harmonic_identity"} & tags:
            add(
                "directed_support",
                0.06*weight*max(context.resolution_strength,0.5),
                "directed harmony favors compact voice-leading support",
            )
        if "altered" in tags and "voice_leading" not in tags:
            add(
                "undirected_tension",
                -0.04*weight,
                "resolution pressure argues against unsupported extra tension",
            )

    elif context.phase is BebopHarmonicPhase.ANTICIPATORY:
        if "rhythm:anticipated" in tags or "anticipation" in tags:
            add(
                "anticipatory_comping",
                0.05*weight*max(context.anticipation_strength,0.5),
                "known future harmony can support an anticipated comping gesture",
            )

    elif context.phase is BebopHarmonicPhase.STABLE_FIELD:
        if action in {"sparse_support","punctuation"}:
            add(
                "stable_field_flexibility",
                0.03*weight,
                "stable harmony permits flexible sparse/punctuating support",
            )

    if (
        context.turn_type is BebopTurnTakingType.COLLECTIVE_RELEASE_REENTRY
        and context.phase is BebopHarmonicPhase.FORM_BOUNDARY
        and role=="lay_out"
    ):
        add(
            "release_boundary_alignment",
            0.05*weight,
            "collective release and form boundary reinforce continued space",
        )

    return BebopHarmonicTurnCompingBias(
        score,
        components,
        tuple(reasons),
    )
