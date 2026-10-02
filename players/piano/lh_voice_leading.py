"""Immediate LH voice-leading continuity for piano comping.

Treat consecutive LH voicings as connected voices rather than unrelated chord grips.
This is piano-local realization logic and does not infer harmony.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .comping import PianoCompingCandidate, PianoCompingState


@dataclass(frozen=True)
class LHVoiceLeadingBias:
    score_delta: float
    components: dict[str,float]
    reasons: tuple[str,...]


def _lh_pitches(candidate: PianoCompingCandidate) -> tuple[int,...]:
    if candidate.realization is None:
        return ()
    hands=dict(candidate.realization.hand_assignment)
    return tuple(sorted(
        voice.pitch_midi
        for voice in candidate.realization.event.voices
        if hands.get(voice.voice_id)=="LH"
    ))


def _last_lh_pitches(state: PianoCompingState) -> tuple[int,...]:
    for candidate in reversed(state.committed):
        pitches=_lh_pitches(candidate)
        if pitches:
            return pitches
    return ()


def evaluate_lh_voice_leading(
    candidate: PianoCompingCandidate,
    state: PianoCompingState,
) -> LHVoiceLeadingBias:
    current=_lh_pitches(candidate)
    previous=_last_lh_pitches(state)
    if not current or not previous:
        return LHVoiceLeadingBias(0.0,{},())

    score=0.0
    components={}
    reasons=[]

    def add(key,value,reason):
        nonlocal score
        score += value
        components[key]=components.get(key,0.0)+value
        reasons.append(reason)

    prev_pcs={p%12 for p in previous}
    cur_pcs={p%12 for p in current}
    common=len(prev_pcs & cur_pcs)
    if common:
        add(
            "lh_common_tone_continuity",
            min(0.06,0.025*common),
            "retaining common tones gives LH harmonic continuity",
        )

    # Greedy nearest-voice motion is adequate as a local continuity diagnostic.
    remaining=list(previous)
    total_motion=0
    matched=0
    for pitch in current:
        if not remaining:
            break
        prev=min(remaining,key=lambda p:abs(pitch-p))
        total_motion += abs(pitch-prev)
        remaining.remove(prev)
        matched += 1

    if matched:
        avg_motion=total_motion/matched
        if avg_motion <= 3.0:
            add(
                "lh_smooth_voice_motion",
                0.07,
                "small LH voice motion supports connected inner harmony",
            )
        elif avg_motion <= 6.0:
            add(
                "lh_moderate_voice_motion",
                0.035,
                "moderate LH motion preserves continuity",
            )
        elif avg_motion >= 10.0:
            add(
                "lh_large_grip_jump",
                -0.055,
                "large LH grip jump weakens voice-leading continuity",
            )

    prev_top=max(previous)
    cur_top=max(current)
    top_motion=abs(cur_top-prev_top)
    if top_motion<=2:
        add(
            "lh_top_voice_line",
            0.035,
            "small top-note motion creates a coherent LH inner line",
        )
    elif top_motion>=9:
        add(
            "lh_top_voice_jump",
            -0.025,
            "large LH top-note jump should be intentional rather than routine",
        )

    return LHVoiceLeadingBias(score,components,tuple(reasons))
