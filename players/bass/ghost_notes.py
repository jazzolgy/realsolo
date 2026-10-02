"""Walking-bass eighth-note ghost/dead-note intelligence.

Ghost notes are rhythmic/percussive bass events, not extra harmonic notes.
They live on the current shared groove, may be chosen only at the current
offbeat, and never pre-compose a future bass figure.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.reasoning.groove_context import GrooveFeel, GrooveTemporalContext
from music_intelligence.reasoning.legend_style_core import CandidateEvent

from .interaction_grammar import BassInteractionDecision, BassInteractionIntent
from .performance_memory import (
    BassArticulation,
    BassCommittedAction,
    BassPerformanceMemory,
    BassPerformanceSnapshot,
)


@dataclass(frozen=True)
class BassGhostContext:
    mode: str = "walking"
    beat_in_measure: float = 0.0
    meter_numerator: int = 4
    tempo_bpm: float = 120.0
    groove: GrooveTemporalContext | None = None
    memory: BassPerformanceSnapshot = BassPerformanceSnapshot()
    interaction: BassInteractionDecision | None = None
    ensemble_activity: float = 0.5
    opportunity_hint: float = 0.0

    def validate(self) -> None:
        if self.meter_numerator <= 0:
            raise ValueError("meter_numerator must be positive")
        if not 0.0 <= self.beat_in_measure < self.meter_numerator:
            raise ValueError("beat_in_measure must be inside the bar")
        if self.tempo_bpm <= 0:
            raise ValueError("tempo_bpm must be positive")
        if not 0.0 <= self.ensemble_activity <= 1.0:
            raise ValueError("ensemble_activity must be within 0..1")
        if not 0.0 <= self.opportunity_hint <= 1.0:
            raise ValueError("opportunity_hint must be within 0..1")
        if self.groove is not None:
            self.groove.validate()


@dataclass(frozen=True)
class BassGhostDecision:
    play: bool
    physical_pitch_midi: int | None
    rhythmic_value_beats: float = 0.5
    sounding_duration_beats: float = 0.16
    velocity: int = 34
    articulation: BassArticulation = BassArticulation.GHOSTED
    score: float = 0.0
    reasons: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.play and self.physical_pitch_midi is None:
            raise ValueError("played ghost note needs a physical string pitch reference")
        if self.physical_pitch_midi is not None and not 0 <= self.physical_pitch_midi <= 127:
            raise ValueError("physical_pitch_midi must be in MIDI range")
        if self.rhythmic_value_beats <= 0:
            raise ValueError("rhythmic value must be positive")
        if self.sounding_duration_beats <= 0:
            raise ValueError("sounding duration must be positive")
        if not 1 <= self.velocity <= 127:
            raise ValueError("velocity must be in MIDI range")


def _is_eighth_offbeat(ctx: BassGhostContext) -> bool:
    """Recognize the current shared eighth-note offbeat.

    For swing/shuffle the caller should invoke this at the warped offbeat from
    Shared GrooveTemporalContext. Straight contexts accept the nominal 0.5.
    """
    frac=ctx.beat_in_measure % 1.0
    if ctx.groove is not None and ctx.groove.feel in {GrooveFeel.SWING, GrooveFeel.SHUFFLE}:
        target=ctx.groove.swing_offbeat_fraction
    else:
        target=.5
    return abs(frac-target) <= .06


def choose_walking_ghost_note(ctx: BassGhostContext) -> BassGhostDecision:
    """Choose one current ghost/dead-note event or SPACE.

    This is deliberately a soft-density decision. Walking quarter notes remain
    the harmonic spine; ghost notes add rhythmic propulsion only when there is
    enough space and recent articulation does not already feel busy.
    """
    ctx.validate()
    reasons: list[str]=[]

    if ctx.mode != "walking":
        return BassGhostDecision(False,None,score=-1.0,reasons=("ghost notes limited to walking mode",))
    if not _is_eighth_offbeat(ctx):
        return BassGhostDecision(False,None,score=-1.0,reasons=("not at shared eighth-note offbeat",))

    score=.18 + .34*ctx.opportunity_hint
    reasons.append("walking offbeat ghost candidate")

    # After beats 2 and 4 (zero-based integer part 1/3) is a particularly useful
    # place for conversational propulsion without replacing the quarter-note line.
    beat_index=int(ctx.beat_in_measure)
    if beat_index % 2 == 1:
        score += .12
        reasons.append("back-half swing pulse supports light propulsion")
    else:
        score -= .035

    if ctx.interaction is not None:
        intent=ctx.interaction.intent
        if intent in {
            BassInteractionIntent.PROPEL,
            BassInteractionIntent.BUILD,
            BassInteractionIntent.FILL,
            BassInteractionIntent.CONNECT,
            BassInteractionIntent.ANSWER,
        }:
            score += .12
            reasons.append(f"{intent.value} opens rhythmic ghost-note space")
        elif intent in {
            BassInteractionIntent.HOLD,
            BassInteractionIntent.YIELD,
            BassInteractionIntent.RESET,
        }:
            score -= .10
            reasons.append(f"{intent.value} restrains ghost-note density")

    # Do not turn walking into constant eighth notes.
    if ctx.memory.recent_ghost_count:
        penalty=.16*min(2,ctx.memory.recent_ghost_count)
        score -= penalty
        reasons.append("recent ghost-note restraint")
    if ctx.memory.recent_complexity >= .62:
        score -= .12
        reasons.append("recent bass complexity favors quarter-note clarity")
    if ctx.ensemble_activity >= .82:
        score -= .10
        reasons.append("dense ensemble leaves less room for bass percussion")
    elif ctx.ensemble_activity <= .42:
        score += .055
        reasons.append("open ensemble texture permits rhythmic detail")

    play=score >= .34
    pitch=ctx.memory.previous_pitch_midi
    if pitch is None:
        pitch=40

    # A ghost note represents a notional eighth-note rhythmic slot but is
    # physically much shorter than a pitched eighth note.
    articulation=(
        BassArticulation.DEAD
        if ctx.memory.recent_ghost_count % 2 == 1
        else BassArticulation.GHOSTED
    )
    velocity=max(24,min(46,round(28+18*max(0.0,min(1.0,score)))))
    duration=.13 if articulation is BassArticulation.DEAD else .17

    out=BassGhostDecision(
        play=play,
        physical_pitch_midi=pitch if play else None,
        rhythmic_value_beats=.5,
        sounding_duration_beats=duration,
        velocity=velocity,
        articulation=articulation,
        score=score,
        reasons=tuple(reasons),
    )
    out.validate()
    return out


def commit_walking_ghost(
    memory: BassPerformanceMemory,
    decision: BassGhostDecision,
) -> None:
    """Remember an actually played ghost without corrupting pitched contour."""
    decision.validate()
    if not decision.play:
        return
    event=CandidateEvent(
        None,
        decision.rhythmic_value_beats,
        tags=frozenset({"bass","walking","ghost_note","eighth_offbeat",decision.articulation.value}),
        source_family="bass_walking_ghost",
    )
    memory.commit(BassCommittedAction(
        event=event,
        accent=max(.12,min(.42,decision.velocity/127.0)),
        sounding_length_ratio=min(1.0,decision.sounding_duration_beats/decision.rhythmic_value_beats),
        articulation=decision.articulation,
        interaction_role="propel",
        harmonic_role="percussive_ghost",
        metric_role="eighth_offbeat",
    ))
