"""Bass-specific realization of Shared Solo Grammar.

This module turns instrument-neutral solo-development operations into immediate
bass behavior without precomposing future phrases.

The state stores only already-committed material and abstract motif/rhythm
summaries. It is therefore compatible with the project's causal
commit -> listen -> replan invariant.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from music_intelligence.reasoning.legend_style_core import CandidateEvent
from music_intelligence.reasoning.solo_grammar import (
    SoloDevelopmentOperation,
    SoloMethodOption,
)


class BassSoloCandidateFamily(str, Enum):
    STATEMENT = "statement"
    MOTIF_RECALL = "motif_recall"
    MOTIF_VARIATION = "motif_variation"
    FRAGMENT = "fragment"
    SEQUENCE = "sequence"
    RHYTHMIC_DISPLACEMENT = "rhythmic_displacement"
    REGISTER_SHIFT = "register_shift"
    HARMONIC_TARGET = "harmonic_target"
    TENSION_EXTENSION = "tension_extension"
    CONTRAST = "contrast"
    SPACE = "space"


@dataclass(frozen=True)
class BassSoloSnapshot:
    recent_pitches: tuple[int, ...] = ()
    recent_intervals: tuple[int, ...] = ()
    recent_durations: tuple[float, ...] = ()
    recent_operations: tuple[SoloDevelopmentOperation, ...] = ()
    motif_intervals: tuple[int, ...] = ()
    motif_durations: tuple[float, ...] = ()
    repetition_count: int = 0

    @property
    def previous_pitch(self) -> int | None:
        return self.recent_pitches[-1] if self.recent_pitches else None


@dataclass
class BassSoloMemory:
    events: list[CandidateEvent] = field(default_factory=list)
    operations: list[SoloDevelopmentOperation] = field(default_factory=list)
    history_limit: int = 32

    def commit(
        self,
        event: CandidateEvent,
        operation: SoloDevelopmentOperation,
    ) -> None:
        self.events.append(event)
        self.operations.append(operation)
        if len(self.events) > self.history_limit:
            self.events[:] = self.events[-self.history_limit:]
        if len(self.operations) > self.history_limit:
            self.operations[:] = self.operations[-self.history_limit:]

    def snapshot(self) -> BassSoloSnapshot:
        pitched = tuple(
            e.pitch_midi for e in self.events[-8:] if e.pitch_midi is not None
        )
        intervals = tuple(b - a for a, b in zip(pitched, pitched[1:]))
        durations = tuple(e.duration_beats for e in self.events[-8:])

        # Active motif is intentionally abstract and short. It is derived only
        # from committed events, never from a future template.
        motif_intervals = intervals[-3:]
        motif_durations = durations[-4:]

        # recent_repetition_count means motif-identity repetition, not
        # "the same operation happened several times".  Repeated STATE/VARY
        # actions must not suppress a later intentional REPEAT.
        repetition = 0
        if self.operations and self.operations[-1] in {
            SoloDevelopmentOperation.REPEAT,
            SoloDevelopmentOperation.RECAP,
        }:
            for op in reversed(self.operations):
                if op in {
                    SoloDevelopmentOperation.REPEAT,
                    SoloDevelopmentOperation.RECAP,
                }:
                    repetition += 1
                else:
                    break

        return BassSoloSnapshot(
            recent_pitches=pitched,
            recent_intervals=intervals,
            recent_durations=durations,
            recent_operations=tuple(self.operations[-8:]),
            motif_intervals=motif_intervals,
            motif_durations=motif_durations,
            repetition_count=repetition,
        )


@dataclass(frozen=True)
class BassSoloPlan:
    operation: SoloDevelopmentOperation
    family: BassSoloCandidateFamily
    duration_beats: float = 1.0
    onset_offset_beats: float = 0.0
    preferred_interval: int | None = None
    register_shift_semitones: int = 0
    tension_bias: float = 0.0
    space_probability: float = 0.0
    reasons: tuple[str, ...] = ()

    @property
    def permits_rest(self) -> bool:
        return self.family is BassSoloCandidateFamily.SPACE or self.space_probability > .5


_OP_FAMILY = {
    SoloDevelopmentOperation.STATE: BassSoloCandidateFamily.STATEMENT,
    SoloDevelopmentOperation.REPEAT: BassSoloCandidateFamily.MOTIF_RECALL,
    SoloDevelopmentOperation.RECAP: BassSoloCandidateFamily.MOTIF_RECALL,
    SoloDevelopmentOperation.VARY: BassSoloCandidateFamily.MOTIF_VARIATION,
    SoloDevelopmentOperation.FRAGMENT: BassSoloCandidateFamily.FRAGMENT,
    SoloDevelopmentOperation.SEQUENCE: BassSoloCandidateFamily.SEQUENCE,
    SoloDevelopmentOperation.DISPLACE: BassSoloCandidateFamily.RHYTHMIC_DISPLACEMENT,
    SoloDevelopmentOperation.CHANGE_REGISTER: BassSoloCandidateFamily.REGISTER_SHIFT,
    SoloDevelopmentOperation.TARGET_NEXT_HARMONY: BassSoloCandidateFamily.HARMONIC_TARGET,
    SoloDevelopmentOperation.RESOLVE: BassSoloCandidateFamily.HARMONIC_TARGET,
    SoloDevelopmentOperation.EXTEND: BassSoloCandidateFamily.TENSION_EXTENSION,
    SoloDevelopmentOperation.AUGMENT: BassSoloCandidateFamily.TENSION_EXTENSION,
    SoloDevelopmentOperation.DIMINISH: BassSoloCandidateFamily.MOTIF_VARIATION,
    SoloDevelopmentOperation.CONTRAST: BassSoloCandidateFamily.CONTRAST,
    SoloDevelopmentOperation.ADD_SPACE: BassSoloCandidateFamily.SPACE,
    SoloDevelopmentOperation.INTERNAL_REST: BassSoloCandidateFamily.SPACE,
    SoloDevelopmentOperation.ANSWER: BassSoloCandidateFamily.MOTIF_VARIATION,
    SoloDevelopmentOperation.INVERT: BassSoloCandidateFamily.MOTIF_VARIATION,
    SoloDevelopmentOperation.CONTRACT: BassSoloCandidateFamily.FRAGMENT,
    SoloDevelopmentOperation.REORCHESTRATE: BassSoloCandidateFamily.REGISTER_SHIFT,
}


def _adjusted_weight(
    option: SoloMethodOption,
    snapshot: BassSoloSnapshot,
) -> float:
    score = option.weight

    # Do not ask for motif manipulation before the player has actually stated
    # enough material to remember.
    if len(snapshot.recent_pitches) < 3 and option.operation in {
        SoloDevelopmentOperation.REPEAT,
        SoloDevelopmentOperation.VARY,
        SoloDevelopmentOperation.FRAGMENT,
        SoloDevelopmentOperation.SEQUENCE,
        SoloDevelopmentOperation.RECAP,
        SoloDevelopmentOperation.INVERT,
    }:
        score -= .22

    # Repetition identity is allowed, but not an endless operation loop.
    if snapshot.recent_operations and option.operation is snapshot.recent_operations[-1]:
        score -= .08 * min(3, snapshot.repetition_count)

    # Rhythmic monotony debt: several consecutive long events create a soft
    # reason to vary/fragment/displace/diminish. This is not randomization; it
    # prevents motif identity from collapsing back into quarter-note-only solo.
    long_surface = (
        len(snapshot.recent_durations) >= 3
        and all(x >= 1.0 for x in snapshot.recent_durations[-3:])
    )
    if long_surface and option.operation in {
        SoloDevelopmentOperation.VARY,
        SoloDevelopmentOperation.FRAGMENT,
        SoloDevelopmentOperation.DISPLACE,
        SoloDevelopmentOperation.DIMINISH,
    }:
        score += .09
    elif long_surface and option.operation is SoloDevelopmentOperation.REPEAT:
        score -= .04

    # Once there is a motif, make actual development more likely than another
    # generic statement.
    if len(snapshot.motif_intervals) >= 2 and option.operation in {
        SoloDevelopmentOperation.VARY,
        SoloDevelopmentOperation.FRAGMENT,
        SoloDevelopmentOperation.SEQUENCE,
        SoloDevelopmentOperation.RECAP,
    }:
        score += .08

    return score


def choose_bass_solo_plan(
    options: tuple[SoloMethodOption, ...],
    snapshot: BassSoloSnapshot,
    *,
    phrase_direction: str = "stable",
) -> BassSoloPlan:
    if not options:
        raise ValueError("solo method options required")

    chosen = max(options, key=lambda x: (_adjusted_weight(x, snapshot), x.operation.value))
    op = chosen.operation

    # Bootstrap with a statement until there is material worth developing.
    if len(snapshot.recent_pitches) < 2 and op not in {
        SoloDevelopmentOperation.ADD_SPACE,
        SoloDevelopmentOperation.INTERNAL_REST,
        SoloDevelopmentOperation.TARGET_NEXT_HARMONY,
    }:
        op = SoloDevelopmentOperation.STATE

    family = _OP_FAMILY.get(op, BassSoloCandidateFamily.STATEMENT)
    duration = 1.0
    onset = 0.0
    preferred_interval: int | None = None
    register_shift = 0
    tension = 0.0
    space = 0.0
    reasons = [f"Shared Solo Grammar -> {op.value}"]

    if op in {SoloDevelopmentOperation.REPEAT, SoloDevelopmentOperation.RECAP}:
        if snapshot.motif_intervals:
            preferred_interval = snapshot.motif_intervals[0]
        if snapshot.motif_durations:
            duration = snapshot.motif_durations[0]
        reasons.append("recall committed motif identity")

    elif op in {SoloDevelopmentOperation.VARY, SoloDevelopmentOperation.ANSWER}:
        if snapshot.motif_intervals:
            preferred_interval = snapshot.motif_intervals[-1]
        duration = .5 if snapshot.recent_durations and snapshot.recent_durations[-1] >= 1.0 else 1.0
        reasons.append("preserve contour identity while allowing interval change")

    elif op is SoloDevelopmentOperation.FRAGMENT:
        if snapshot.motif_intervals:
            preferred_interval = snapshot.motif_intervals[-1]
        duration = .5
        reasons.append("use a short committed-material fragment")

    elif op is SoloDevelopmentOperation.SEQUENCE:
        if snapshot.recent_intervals:
            preferred_interval = snapshot.recent_intervals[-1]
        duration = .5
        reasons.append("continue intervallic direction as a sequence")

    elif op is SoloDevelopmentOperation.DISPLACE:
        duration = .5
        onset = .25
        reasons.append("shift event placement away from the quarter-note grid")

    elif op in {SoloDevelopmentOperation.CHANGE_REGISTER, SoloDevelopmentOperation.REORCHESTRATE}:
        register_shift = 12 if phrase_direction != "fall" else -12
        duration = .75
        reasons.append("register becomes phrase-forming material")

    elif op in {SoloDevelopmentOperation.EXTEND, SoloDevelopmentOperation.AUGMENT}:
        duration = 1.5
        tension = .16
        reasons.append("prolong melodic/tensional identity across local harmony")

    elif op is SoloDevelopmentOperation.DIMINISH:
        duration = .5
        reasons.append("increase event density without changing phrase identity")

    elif op is SoloDevelopmentOperation.CONTRAST:
        preferred_interval = 7
        duration = .75
        tension = .10
        reasons.append("contrast recent contour/register behavior")

    elif op in {SoloDevelopmentOperation.TARGET_NEXT_HARMONY, SoloDevelopmentOperation.RESOLVE}:
        duration = 1.0
        tension = -.10
        reasons.append("reconnect phrase to structural harmony")

    elif op in {SoloDevelopmentOperation.ADD_SPACE, SoloDevelopmentOperation.INTERNAL_REST}:
        duration = 1.0
        space = 1.0
        reasons.append("silence is an active solo-development event")

    return BassSoloPlan(
        operation=op,
        family=family,
        duration_beats=duration,
        onset_offset_beats=onset,
        preferred_interval=preferred_interval,
        register_shift_semitones=register_shift,
        tension_bias=tension,
        space_probability=space,
        reasons=tuple(reasons),
    )


def bass_solo_candidate_score(
    plan: BassSoloPlan,
    snapshot: BassSoloSnapshot,
    *,
    pitch: int,
    structural: bool,
) -> tuple[float, tuple[str, ...]]:
    """Score one immediate pitched candidate against the current solo plan."""
    score = 0.0
    reasons: list[str] = []
    previous = snapshot.previous_pitch
    delta = pitch - previous if previous is not None else None

    if plan.family is BassSoloCandidateFamily.HARMONIC_TARGET:
        score += .09 if structural else -.06
        reasons.append("solo plan reconnects to structural harmony")

    elif plan.family is BassSoloCandidateFamily.TENSION_EXTENSION:
        score += .05 if not structural else .01
        reasons.append("solo plan permits tension to outlive local chord spelling")

    elif plan.family is BassSoloCandidateFamily.REGISTER_SHIFT and previous is not None:
        target = previous + plan.register_shift_semitones
        score += max(-.08, .13 - .015 * abs(pitch - target))
        reasons.append("solo plan shapes a register-level phrase event")

    elif plan.family is BassSoloCandidateFamily.CONTRAST and delta is not None:
        if abs(delta) >= 5:
            score += .09
            reasons.append("contrast favors a larger intervallic break")

    if plan.preferred_interval is not None and delta is not None:
        target = plan.preferred_interval
        if plan.family is BassSoloCandidateFamily.MOTIF_RECALL:
            score += max(-.06, .12 - .025 * abs(delta - target))
            reasons.append("candidate recalls committed motif interval")
        elif plan.family in {
            BassSoloCandidateFamily.MOTIF_VARIATION,
            BassSoloCandidateFamily.FRAGMENT,
            BassSoloCandidateFamily.SEQUENCE,
        }:
            same_direction = (target > 0 and delta > 0) or (target < 0 and delta < 0)
            if same_direction:
                score += .07
                reasons.append("candidate preserves motif contour direction")
            if delta == target:
                score += .025

    if plan.family is BassSoloCandidateFamily.RHYTHMIC_DISPLACEMENT:
        score += .02
        reasons.append("pitch remains secondary to rhythmic displacement")

    return score, tuple(reasons)
