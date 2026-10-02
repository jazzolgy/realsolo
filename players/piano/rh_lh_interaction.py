"""Immediate RH-LH rhythmic relationship evaluator for piano-led trio playing.

This module does not schedule a future two-hand phrase. It evaluates only the current
LH comping candidate against recently observed/current RH foreground timing evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from .ensemble_role import PianoEnsembleMode

if TYPE_CHECKING:
    from .comping import PianoCompingCandidate, PianoCompingContext


class RHLHRelation(str, Enum):
    LAY_OUT = "lay_out"
    SIMULTANEOUS_SUPPORT = "simultaneous_support"
    DELAYED_RESPONSE = "delayed_response"
    PHRASE_GAP_ANSWER = "phrase_gap_answer"
    SUSTAIN_UNDER_LINE = "sustain_under_line"
    INTENTIONAL_DOUBLING = "intentional_doubling"
    INDEPENDENT_PUNCTUATION = "independent_punctuation"


@dataclass(frozen=True)
class RHLHInteractionBias:
    relation: RHLHRelation
    score_delta: float
    components: dict[str,float]
    reasons: tuple[str,...]


def evaluate_rh_lh_interaction(
    candidate: "PianoCompingCandidate",
    context: "PianoCompingContext",
) -> RHLHInteractionBias:
    context.validate()

    if context.ensemble_mode not in {
        PianoEnsembleMode.PIANO_HEAD_TRIO,
        PianoEnsembleMode.PIANO_SOLO_TRIO,
    }:
        return RHLHInteractionBias(
            RHLHRelation.INDEPENDENT_PUNCTUATION,0.0,{},()
        )

    if candidate.realization is None:
        relation=RHLHRelation.LAY_OUT
        score=0.0
        components={}
        reasons=[]
        if context.piano_foreground_activity>=0.78:
            score += .08
            components["rh_lh_busy_lay_out"]=.08
            reasons.append("active RH foreground can justify complete LH space")
        return RHLHInteractionBias(relation,score,components,tuple(reasons))

    event=candidate.realization.event
    onset=float(event.onset_offset_beats)
    duration=float(event.duration_beats)
    recent_onset=context.piano_foreground_onset_proximity_beats
    gap=context.piano_foreground_gap_beats
    match=context.piano_foreground_rhythm_match_confidence
    busy=context.piano_foreground_activity>=0.72

    score=0.0
    components={}
    reasons=[]

    def add(key,value,reason):
        nonlocal score
        score += value
        components[key]=components.get(key,0.0)+value
        reasons.append(reason)

    simultaneous = recent_onset is not None and recent_onset <= .125 and abs(onset) <= .125

    if simultaneous and match>=.75:
        relation=RHLHRelation.INTENTIONAL_DOUBLING
        add(
            "rh_lh_intentional_doubling",
            .085,
            "strong rhythmic/motivic match supports intentional RH-LH doubling",
        )
    elif simultaneous:
        relation=RHLHRelation.SIMULTANEOUS_SUPPORT
        if busy:
            add(
                "rh_lh_unnecessary_unison_attack",
                -.075,
                "routine simultaneous LH attack can stiffen an active RH phrase",
            )
        else:
            add(
                "rh_lh_simultaneous_support",
                .015,
                "simultaneous support remains available when RH is not crowded",
            )
    elif recent_onset is not None and recent_onset <= .5 and onset >= .125:
        relation=RHLHRelation.DELAYED_RESPONSE
        add(
            "rh_lh_delayed_response",
            .07,
            "LH delayed response creates independence from the recent RH attack",
        )
    elif gap >= .5 and onset >= 0:
        relation=RHLHRelation.PHRASE_GAP_ANSWER
        add(
            "rh_lh_phrase_gap_answer",
            .09,
            "LH answer uses space left by the RH phrase",
        )
    elif busy and duration >= 1.0 and abs(onset)<=.125:
        relation=RHLHRelation.SUSTAIN_UNDER_LINE
        add(
            "rh_lh_sustain_under_line",
            .035,
            "sustained LH color can support an active RH line without repeated attacks",
        )
    else:
        relation=RHLHRelation.INDEPENDENT_PUNCTUATION
        if abs(onset)>=.125:
            add(
                "rh_lh_independent_timing",
                .035,
                "non-simultaneous LH placement preserves two-hand rhythmic independence",
            )

    if match < .35 and simultaneous and busy:
        add(
            "rh_lh_weak_doubling_evidence",
            -.035,
            "simultaneous attack lacks evidence of intentional rhythmic doubling",
        )

    return RHLHInteractionBias(relation,score,components,tuple(reasons))
