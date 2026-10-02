"""v1.36 shared voice-leading intelligence.

This module models voice-leading as semantic musical relationships rather than
nearest-note geometry alone. It is instrument-neutral and suitable for melody,
voicing, horn writing, arranging, and ensemble reasoning.

No exact future line or future voicing sequence is stored here. The layer
evaluates immediate current-to-next voice relationships and unresolved
tendencies that may inform later candidate scoring.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import inf
from typing import Sequence


class MotionType(str, Enum):
    COMMON_TONE = "common_tone"
    STEP = "step"
    LEAP = "leap"
    CONTRARY = "contrary"
    OBLIQUE = "oblique"
    PARALLEL = "parallel"
    SIMILAR = "similar"
    UNKNOWN = "unknown"


class VoiceRole(str, Enum):
    BASS = "bass"
    INNER = "inner"
    TOP = "top"
    MELODY = "melody"
    GENERIC = "generic"


class TargetRole(str, Enum):
    ROOT = "root"
    THIRD = "third"
    FIFTH = "fifth"
    SEVENTH = "seventh"
    GUIDE_TONE = "guide_tone"
    TENSION = "tension"
    STRUCTURAL = "structural"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class VoiceState:
    voice_id: str
    pitch_midi: int
    role: VoiceRole = VoiceRole.GENERIC
    harmonic_role: TargetRole = TargetRole.UNKNOWN
    pitch_class: int | None = None

    def validate(self) -> None:
        if not self.voice_id:
            raise ValueError("voice_id is required")
        if not 0 <= self.pitch_midi <= 127:
            raise ValueError("pitch_midi must be in 0..127")

    @property
    def pc(self) -> int:
        return self.pitch_class if self.pitch_class is not None else self.pitch_midi % 12


@dataclass(frozen=True)
class VoiceMotion:
    from_voice_id: str
    to_voice_id: str
    semitones: int
    abs_semitones: int
    common_tone: bool
    stepwise: bool
    leap: bool
    role_continuity: bool
    target_role: TargetRole
    attraction: float = 0.0
    resolution_credit: float = 0.0
    cost: float = 0.0
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolutionDebt:
    voice_id: str
    source_pitch_midi: int
    tendency: str
    target_pitch_classes: tuple[int, ...]
    urgency: float
    age_events: int = 0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.voice_id:
            raise ValueError("voice_id is required")
        if not 0 <= self.source_pitch_midi <= 127:
            raise ValueError("source_pitch_midi must be in 0..127")
        if any(not 0 <= pc <= 11 for pc in self.target_pitch_classes):
            raise ValueError("target pitch classes must be in 0..11")
        if not 0.0 <= self.urgency <= 1.0:
            raise ValueError("urgency must be within 0..1")
        if self.age_events < 0:
            raise ValueError("age_events may not be negative")

    def advanced(self) -> "ResolutionDebt":
        return ResolutionDebt(
            self.voice_id,
            self.source_pitch_midi,
            self.tendency,
            self.target_pitch_classes,
            self.urgency,
            self.age_events + 1,
            self.provenance,
        )


@dataclass(frozen=True)
class VoiceLeadingContext:
    current: tuple[VoiceState, ...]
    candidate: tuple[VoiceState, ...]
    debts: tuple[ResolutionDebt, ...] = ()
    preserve_voice_identity: bool = True
    prefer_common_tones: bool = True
    prefer_stepwise: bool = True
    top_line_continuity: float = 0.5
    bass_direction_weight: float = 0.5
    target_pitch_classes: frozenset[int] = frozenset()
    target_roles: frozenset[TargetRole] = frozenset()

    def validate(self) -> None:
        for v in self.current + self.candidate:
            v.validate()
        ids = [v.voice_id for v in self.candidate]
        if len(ids) != len(set(ids)):
            raise ValueError("candidate voice ids must be unique")
        if not 0.0 <= self.top_line_continuity <= 1.0:
            raise ValueError("top_line_continuity must be within 0..1")
        if not 0.0 <= self.bass_direction_weight <= 1.0:
            raise ValueError("bass_direction_weight must be within 0..1")
        for debt in self.debts:
            debt.validate()


@dataclass(frozen=True)
class VoiceLeadingAssessment:
    motions: tuple[VoiceMotion, ...]
    common_tone_count: int
    stepwise_count: int
    total_motion_semitones: int
    max_motion_semitones: int
    top_line_motion_semitones: int | None
    bass_motion_semitones: int | None
    contrary_or_oblique_bonus: float
    parallel_perfect_penalty: float
    debt_resolution_credit: float
    unresolved_debt_penalty: float
    target_arrival_credit: float
    total_score: float
    remaining_debts: tuple[ResolutionDebt, ...]


def _by_id(voices: Sequence[VoiceState]) -> dict[str, VoiceState]:
    return {v.voice_id: v for v in voices}


def _motion_cost(delta: int, prefer_stepwise: bool) -> float:
    a = abs(delta)
    if a == 0:
        return 0.0
    if a <= 2:
        return .03 * a if prefer_stepwise else .05 * a
    if a <= 5:
        return .10 + .04 * (a - 2)
    return .24 + .07 * (a - 5)


def _role_attraction(target_role: TargetRole) -> float:
    if target_role is TargetRole.GUIDE_TONE:
        return .16
    if target_role in {TargetRole.THIRD, TargetRole.SEVENTH}:
        return .12
    if target_role in {TargetRole.ROOT, TargetRole.STRUCTURAL}:
        return .08
    if target_role is TargetRole.TENSION:
        return .02
    return 0.0


def _pair_by_identity_or_nearest(
    current: Sequence[VoiceState],
    candidate: Sequence[VoiceState],
    preserve_identity: bool,
) -> tuple[tuple[VoiceState, VoiceState], ...]:
    cur = _by_id(current)
    pairs: list[tuple[VoiceState, VoiceState]] = []
    used: set[str] = set()

    for nxt in candidate:
        prev = cur.get(nxt.voice_id)
        if prev is not None:
            pairs.append((prev, nxt))
            used.add(prev.voice_id)

    if preserve_identity:
        return tuple(pairs)

    leftovers = [v for v in current if v.voice_id not in used]
    paired_next = {b.voice_id for _, b in pairs}
    for nxt in (v for v in candidate if v.voice_id not in paired_next):
        if not leftovers:
            break
        prev = min(leftovers, key=lambda x: abs(x.pitch_midi - nxt.pitch_midi))
        leftovers.remove(prev)
        pairs.append((prev, nxt))
    return tuple(pairs)


def _outer_motion_type(
    current: Sequence[VoiceState],
    candidate: Sequence[VoiceState],
) -> MotionType:
    cur_top = next((v for v in current if v.role in {VoiceRole.TOP, VoiceRole.MELODY}), None)
    nxt_top = next((v for v in candidate if v.voice_id == (cur_top.voice_id if cur_top else "")), None)
    cur_bass = next((v for v in current if v.role is VoiceRole.BASS), None)
    nxt_bass = next((v for v in candidate if v.voice_id == (cur_bass.voice_id if cur_bass else "")), None)
    if not all((cur_top, nxt_top, cur_bass, nxt_bass)):
        return MotionType.UNKNOWN

    t = nxt_top.pitch_midi - cur_top.pitch_midi
    b = nxt_bass.pitch_midi - cur_bass.pitch_midi
    if t == 0 or b == 0:
        return MotionType.OBLIQUE
    if t * b < 0:
        return MotionType.CONTRARY
    if t == b:
        return MotionType.PARALLEL
    return MotionType.SIMILAR


def _perfect_interval(pc_distance: int) -> bool:
    return pc_distance % 12 in {0, 7}


def _parallel_perfect_penalty(
    current: Sequence[VoiceState],
    candidate: Sequence[VoiceState],
) -> float:
    cur = _by_id(current)
    nxt = _by_id(candidate)
    shared = [vid for vid in cur if vid in nxt]
    penalty = 0.0
    for i, a in enumerate(shared):
        for b in shared[i + 1:]:
            before = abs(cur[a].pitch_midi - cur[b].pitch_midi) % 12
            after = abs(nxt[a].pitch_midi - nxt[b].pitch_midi) % 12
            da = nxt[a].pitch_midi - cur[a].pitch_midi
            db = nxt[b].pitch_midi - cur[b].pitch_midi
            if da != 0 and db != 0 and (da > 0) == (db > 0):
                if _perfect_interval(before) and _perfect_interval(after):
                    penalty += .10
    return penalty


def _resolve_debts(
    candidate: Sequence[VoiceState],
    debts: Sequence[ResolutionDebt],
) -> tuple[float, float, tuple[ResolutionDebt, ...]]:
    nxt = _by_id(candidate)
    credit = 0.0
    penalty = 0.0
    remaining: list[ResolutionDebt] = []
    for debt in debts:
        voice = nxt.get(debt.voice_id)
        if voice is not None and voice.pc in debt.target_pitch_classes:
            credit += .18 * debt.urgency
            continue
        advanced = debt.advanced()
        remaining.append(advanced)
        penalty += min(.22, .04 * advanced.age_events) * debt.urgency
    return credit, penalty, tuple(remaining)


def assess_voice_leading(ctx: VoiceLeadingContext) -> VoiceLeadingAssessment:
    ctx.validate()
    pairs = _pair_by_identity_or_nearest(
        ctx.current, ctx.candidate, ctx.preserve_voice_identity
    )

    motions: list[VoiceMotion] = []
    common = stepwise = total_motion = max_motion = 0
    target_credit = 0.0

    for prev, nxt in pairs:
        delta = nxt.pitch_midi - prev.pitch_midi
        a = abs(delta)
        is_common = a == 0
        is_step = 0 < a <= 2
        is_leap = a >= 6
        common += int(is_common)
        stepwise += int(is_step)
        total_motion += a
        max_motion = max(max_motion, a)

        attraction = _role_attraction(nxt.harmonic_role)
        if nxt.pc in ctx.target_pitch_classes:
            attraction += .10
        if nxt.harmonic_role in ctx.target_roles:
            attraction += .08
        target_credit += attraction

        cost = _motion_cost(delta, ctx.prefer_stepwise)
        reasons: list[str] = []
        if is_common and ctx.prefer_common_tones:
            cost -= .08
            reasons.append("common-tone retention")
        if is_step:
            cost -= .05
            reasons.append("stepwise continuity")
        if nxt.harmonic_role is TargetRole.GUIDE_TONE:
            reasons.append("guide-tone arrival")
        if attraction:
            reasons.append("structural target attraction")

        motions.append(VoiceMotion(
            prev.voice_id,
            nxt.voice_id,
            delta,
            a,
            is_common,
            is_step,
            is_leap,
            prev.voice_id == nxt.voice_id,
            nxt.harmonic_role,
            attraction=attraction,
            resolution_credit=0.0,
            cost=max(0.0, cost),
            reasons=tuple(reasons),
        ))

    outer = _outer_motion_type(ctx.current, ctx.candidate)
    contrary_bonus = .0
    if outer is MotionType.CONTRARY:
        contrary_bonus = .10
    elif outer is MotionType.OBLIQUE:
        contrary_bonus = .07

    parallel_penalty = _parallel_perfect_penalty(ctx.current, ctx.candidate)

    debt_credit, debt_penalty, remaining = _resolve_debts(ctx.candidate, ctx.debts)

    top_motion = None
    bass_motion = None
    for m in motions:
        prev = next(v for v in ctx.current if v.voice_id == m.from_voice_id)
        if prev.role in {VoiceRole.TOP, VoiceRole.MELODY}:
            top_motion = m.abs_semitones
        if prev.role is VoiceRole.BASS:
            bass_motion = m.abs_semitones

    motion_cost = sum(m.cost for m in motions)
    continuity_bonus = (
        common * (.08 if ctx.prefer_common_tones else .03)
        + stepwise * (.05 if ctx.prefer_stepwise else .02)
    )
    if top_motion is not None:
        continuity_bonus += max(0.0, .12 - .02 * top_motion) * ctx.top_line_continuity
    if bass_motion is not None:
        motion_cost += max(0.0, bass_motion - 7) * .015 * ctx.bass_direction_weight

    total_score = (
        continuity_bonus
        + contrary_bonus
        + debt_credit
        + target_credit
        - motion_cost
        - parallel_penalty
        - debt_penalty
    )

    return VoiceLeadingAssessment(
        tuple(motions),
        common,
        stepwise,
        total_motion,
        max_motion,
        top_motion,
        bass_motion,
        contrary_bonus,
        parallel_penalty,
        debt_credit,
        debt_penalty,
        target_credit,
        total_score,
        remaining,
    )


def make_resolution_debt(
    *,
    voice_id: str,
    source_pitch_midi: int,
    tendency: str,
    target_pitch_classes: Sequence[int],
    urgency: float = .7,
    provenance: Sequence[str] = (),
) -> ResolutionDebt:
    debt = ResolutionDebt(
        voice_id,
        source_pitch_midi,
        tendency,
        tuple(target_pitch_classes),
        urgency,
        0,
        tuple(provenance),
    )
    debt.validate()
    return debt
