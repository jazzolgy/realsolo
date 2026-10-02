"""Bass-specific immediate-action realization.

This module consumes Shared Core harmony and voice-leading intelligence. It does
not implement a separate jazz-harmony theory and never precomposes a future bass
line. Each call generates candidates for the next immediate bass action only.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.harmony.jazz_harmony_core import HarmonicFrame, build_basic_affordances
from music_intelligence.harmony.voice_leading import (
    TargetRole,
    VoiceLeadingContext,
    VoiceRole,
    VoiceState,
    assess_voice_leading,
)
from music_intelligence.reasoning.legend_style_core import CandidateEvent


class BassMode(str, Enum):
    WALKING = "walking"
    TWO_FEEL = "two_feel"
    PEDAL = "pedal"
    OSTINATO = "ostinato"


class BassHarmonicRole(str, Enum):
    ROOT = "root"
    FIFTH = "fifth"
    CHORD_TONE = "chord_tone"
    CHROMATIC_APPROACH = "chromatic_approach"
    ANTICIPATION = "anticipation"
    PEDAL = "pedal"


@dataclass(frozen=True)
class BassContext:
    mode: BassMode = BassMode.WALKING
    beat_in_measure: float = 0.0
    meter_numerator: int = 4
    previous_pitch_midi: int | None = None
    register_low_midi: int = 28
    register_high_midi: int = 55
    ensemble_activity: float = 0.5

    def validate(self) -> None:
        if self.meter_numerator <= 0:
            raise ValueError("meter_numerator must be positive")
        if not 0.0 <= self.beat_in_measure < self.meter_numerator:
            raise ValueError("beat_in_measure must fall inside the current measure")
        if not 0 <= self.register_low_midi <= self.register_high_midi <= 127:
            raise ValueError("invalid bass register")
        if self.previous_pitch_midi is not None and not 0 <= self.previous_pitch_midi <= 127:
            raise ValueError("previous_pitch_midi must be in MIDI range")
        if not 0.0 <= self.ensemble_activity <= 1.0:
            raise ValueError("ensemble_activity must be within 0..1")


@dataclass(frozen=True)
class BassActionCandidate:
    event: CandidateEvent
    harmonic_role: BassHarmonicRole
    target_pitch_class: int
    score: float
    reasons: tuple[str, ...] = ()


def _active_root_pc(frame: HarmonicFrame) -> int | None:
    for evidence in (frame.inferred, frame.observed, frame.expected):
        if evidence is not None and evidence.root_pc is not None:
            return evidence.root_pc
    return None


def _active_pitch_classes(frame: HarmonicFrame) -> frozenset[int]:
    for evidence in (frame.inferred, frame.observed, frame.expected):
        if evidence is not None and evidence.pitch_classes:
            return evidence.pitch_classes
    root = _active_root_pc(frame)
    return frozenset({root}) if root is not None else frozenset()


def _nearest_pitch_for_pc(pc: int, ctx: BassContext) -> int:
    options = [
        p for p in range(ctx.register_low_midi, ctx.register_high_midi + 1)
        if p % 12 == pc % 12
    ]
    if not options:
        raise ValueError("register contains no realization for requested pitch class")
    target = ctx.previous_pitch_midi
    if target is None:
        target = (ctx.register_low_midi + ctx.register_high_midi) / 2
    return min(options, key=lambda p: (abs(p - target), p))


def _duration_for_mode(mode: BassMode) -> float:
    if mode is BassMode.TWO_FEEL:
        return 2.0
    return 1.0


def _voice_role_for(candidate: BassHarmonicRole) -> TargetRole:
    if candidate in {BassHarmonicRole.ROOT, BassHarmonicRole.PEDAL}:
        return TargetRole.ROOT
    if candidate is BassHarmonicRole.FIFTH:
        return TargetRole.FIFTH
    if candidate in {BassHarmonicRole.CHROMATIC_APPROACH, BassHarmonicRole.ANTICIPATION}:
        return TargetRole.STRUCTURAL
    return TargetRole.UNKNOWN


def _shared_voice_leading_score(
    previous_pitch: int | None,
    candidate_pitch: int,
    harmonic_role: BassHarmonicRole,
) -> float:
    if previous_pitch is None:
        return 0.0
    current = VoiceState("bass", previous_pitch, role=VoiceRole.BASS)
    nxt = VoiceState(
        "bass",
        candidate_pitch,
        role=VoiceRole.BASS,
        harmonic_role=_voice_role_for(harmonic_role),
    )
    assessment = assess_voice_leading(VoiceLeadingContext(
        current=(current,),
        candidate=(nxt,),
        bass_direction_weight=0.85,
    ))
    return assessment.total_score


def generate_immediate_bass_candidates(
    frame: HarmonicFrame,
    ctx: BassContext,
) -> tuple[BassActionCandidate, ...]:
    """Generate candidates for one immediate bass action.

    Future harmony may influence an approach/anticipation candidate, but this
    function never returns a fixed multi-note line.
    """
    frame.validate()
    ctx.validate()
    build_basic_affordances(frame)  # validates shared harmonic semantics/affordances

    root_pc = _active_root_pc(frame)
    if root_pc is None:
        return ()

    pcs = _active_pitch_classes(frame)
    duration = _duration_for_mode(ctx.mode)
    raw: list[tuple[int, BassHarmonicRole, float, tuple[str, ...]]] = []

    if ctx.mode is BassMode.PEDAL:
        raw.append((root_pc, BassHarmonicRole.PEDAL, 0.46, ("pedal anchor",)))
    else:
        strong = abs(ctx.beat_in_measure - round(ctx.beat_in_measure)) < 1e-9
        root_weight = 0.44 if strong else 0.34
        raw.append((root_pc, BassHarmonicRole.ROOT, root_weight, ("current harmonic anchor",)))

        fifth_pc = (root_pc + 7) % 12
        if not pcs or fifth_pc in pcs:
            raw.append((
                fifth_pc,
                BassHarmonicRole.FIFTH,
                0.21,
                ("shared evidence supports perfect-fifth option",),
            ))

        if ctx.mode is BassMode.WALKING:
            for pc in sorted(pcs):
                if pc in {root_pc, fifth_pc}:
                    continue
                raw.append((
                    pc,
                    BassHarmonicRole.CHORD_TONE,
                    0.16,
                    ("observed/shared chord-tone option",),
                ))

    next_root = frame.next_expected.root_pc if frame.next_expected is not None else None
    late_measure = ctx.beat_in_measure >= ctx.meter_numerator - 1.0
    if ctx.mode is BassMode.WALKING and next_root is not None and late_measure:
        raw.extend((
            ((next_root - 1) % 12, BassHarmonicRole.CHROMATIC_APPROACH, 0.30,
             ("chromatic lower approach to next expected root",)),
            ((next_root + 1) % 12, BassHarmonicRole.CHROMATIC_APPROACH, 0.25,
             ("chromatic upper approach to next expected root",)),
            (next_root, BassHarmonicRole.ANTICIPATION, 0.20,
             ("direct anticipation of next expected root",)),
        ))

    candidates: list[BassActionCandidate] = []
    seen: set[tuple[int, BassHarmonicRole]] = set()
    for pc, role, base, reasons in raw:
        key = (pc % 12, role)
        if key in seen:
            continue
        seen.add(key)
        pitch = _nearest_pitch_for_pc(pc, ctx)
        vl = _shared_voice_leading_score(ctx.previous_pitch_midi, pitch, role)

        motion_penalty = 0.0
        if ctx.previous_pitch_midi is not None:
            leap = abs(pitch - ctx.previous_pitch_midi)
            if leap > 7:
                motion_penalty = 0.035 * (leap - 7)

        ensemble_space = 0.0
        if ctx.ensemble_activity > 0.8 and role is not BassHarmonicRole.ROOT:
            ensemble_space = -0.04

        tags = {"bass", ctx.mode.value, role.value}
        if role in {
            BassHarmonicRole.ROOT,
            BassHarmonicRole.FIFTH,
            BassHarmonicRole.CHORD_TONE,
            BassHarmonicRole.PEDAL,
        }:
            tags.add("chord_tone")
        if role in {BassHarmonicRole.CHROMATIC_APPROACH, BassHarmonicRole.ANTICIPATION}:
            tags.add("directed_target")
        if role is BassHarmonicRole.ANTICIPATION:
            tags.add("anticipation")

        score = base + vl - motion_penalty + ensemble_space
        candidates.append(BassActionCandidate(
            event=CandidateEvent(
                pitch_midi=pitch,
                duration_beats=duration,
                tags=frozenset(tags),
                source_family="bass_immediate_realization",
            ),
            harmonic_role=role,
            target_pitch_class=pc % 12,
            score=score,
            reasons=reasons + (f"shared voice-leading={vl:.3f}",),
        ))

    return tuple(sorted(candidates, key=lambda x: x.score, reverse=True))


def choose_immediate_bass_action(
    frame: HarmonicFrame,
    ctx: BassContext,
) -> BassActionCandidate:
    candidates = generate_immediate_bass_candidates(frame, ctx)
    if not candidates:
        raise ValueError("no bass candidates for current harmonic frame")
    return candidates[0]
