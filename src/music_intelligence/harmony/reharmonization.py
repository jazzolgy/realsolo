"""v1.38 substitution / reharmonization intelligence.

The source-grounded taxonomy follows the uploaded jazz-harmony materials that
separate secondary dominants, substitute dominants, key-of-the-moment,
interpolated chords, and modal interchange as advanced harmonic resources.

The scoring model below is a UMR architecture abstraction: a reharmonization is
not accepted because a rule-table says it is legal. It is evaluated by how much
musical continuity it preserves or intentionally redirects through target,
voice-leading, bass, common-tone, function, and modal relationships.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class ReharmonizationKind(str, Enum):
    SECONDARY_DOMINANT = "secondary_dominant"
    SUBSTITUTE_DOMINANT = "substitute_dominant"
    EXTENDED_DOMINANT = "extended_dominant"
    MODAL_INTERCHANGE = "modal_interchange"
    INTERPOLATION = "interpolation"
    KEY_OF_THE_MOMENT = "key_of_the_moment"
    DIMINISHED_APPROACH = "diminished_approach"
    CHROMATIC_APPROACH = "chromatic_approach"
    PEDAL_REINTERPRETATION = "pedal_reinterpretation"
    NONFUNCTIONAL_COLOR = "nonfunctional_color"
    UNKNOWN = "unknown"


class ContinuityAxis(str, Enum):
    TARGET_PRESERVATION = "target_preservation"
    FUNCTION_PRESERVATION = "function_preservation"
    COMMON_TONE = "common_tone"
    GUIDE_TONE = "guide_tone"
    VOICE_LEADING = "voice_leading"
    BASS_LOGIC = "bass_logic"
    MELODY_COMPATIBILITY = "melody_compatibility"
    MODAL_BORROWING = "modal_borrowing"
    INTERVAL_SHAPE = "interval_shape"
    NARRATIVE_TENSION = "narrative_tension"


@dataclass(frozen=True)
class HarmonicSnapshot:
    symbol: str | None = None
    root_pc: int | None = None
    pitch_classes: frozenset[int] = frozenset()
    function: str | None = None
    target_root_pc: int | None = None
    bass_pc: int | None = None
    melody_pcs: frozenset[int] = frozenset()
    key_context: str | None = None

    def validate(self) -> None:
        for pc in (
            set(self.pitch_classes)
            | set(self.melody_pcs)
            | ({self.root_pc} if self.root_pc is not None else set())
            | ({self.target_root_pc} if self.target_root_pc is not None else set())
            | ({self.bass_pc} if self.bass_pc is not None else set())
        ):
            if not 0 <= pc <= 11:
                raise ValueError("pitch classes must be in 0..11")


@dataclass(frozen=True)
class ReharmonizationProposal:
    proposal_id: str
    kind: ReharmonizationKind
    original: HarmonicSnapshot
    substitute: HarmonicSnapshot
    axes: frozenset[ContinuityAxis] = frozenset()
    intended_target_pc: int | None = None
    tension_delta: float = 0.0
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()
    note: str = ""

    def validate(self) -> None:
        if not self.proposal_id:
            raise ValueError("proposal_id is required")
        self.original.validate()
        self.substitute.validate()
        if self.intended_target_pc is not None and not 0 <= self.intended_target_pc <= 11:
            raise ValueError("intended_target_pc must be in 0..11")
        if not -1.0 <= self.tension_delta <= 1.0:
            raise ValueError("tension_delta must be within -1..1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


@dataclass(frozen=True)
class ReharmonizationAssessment:
    continuity_score: float
    target_preservation: float
    function_preservation: float
    common_tone_support: float
    voice_leading_support: float
    bass_logic_support: float
    melody_compatibility: float
    modal_borrowing_support: float
    narrative_fit: float
    risk: float
    accepted_axes: tuple[ContinuityAxis, ...]
    reasons: tuple[str, ...]


def _pc_distance(a: int, b: int) -> int:
    d = (b - a) % 12
    return min(d, 12 - d)


def _root_motion_support(a: int | None, b: int | None) -> float:
    if a is None or b is None:
        return .0
    distance = _pc_distance(a, b)
    if distance == 0:
        return 1.0
    if distance in {1, 2}:
        return .82
    if distance in {5, 6}:
        return .60
    return .38


def _common_tone_support(a: frozenset[int], b: frozenset[int]) -> float:
    if not a or not b:
        return .0
    common = len(a & b)
    return min(1.0, common / max(1, min(len(a), len(b))))


def _melody_compatibility(snapshot: HarmonicSnapshot) -> float:
    if not snapshot.melody_pcs:
        return .5
    if not snapshot.pitch_classes:
        return .35
    inside = len(snapshot.melody_pcs & snapshot.pitch_classes)
    return inside / len(snapshot.melody_pcs)


def _target_preservation(p: ReharmonizationProposal) -> float:
    intended = p.intended_target_pc
    if intended is None:
        intended = p.original.target_root_pc
    if intended is None:
        return .5

    sub_target = p.substitute.target_root_pc
    if sub_target is not None:
        if sub_target == intended:
            return 1.0
        return max(0.0, 1.0 - _pc_distance(sub_target, intended) / 6.0)

    if p.substitute.root_pc is not None:
        # Dominant-like approach: fifth-down or semitone-down target relation.
        fifth_target = (p.substitute.root_pc + 5) % 12
        half_target = (p.substitute.root_pc - 1) % 12
        if intended in {fifth_target, half_target}:
            return .90
    return .25


def _function_preservation(p: ReharmonizationProposal) -> float:
    of = (p.original.function or "").lower()
    sf = (p.substitute.function or "").lower()
    if of and sf and of == sf:
        return 1.0
    if p.kind in {
        ReharmonizationKind.SECONDARY_DOMINANT,
        ReharmonizationKind.SUBSTITUTE_DOMINANT,
        ReharmonizationKind.EXTENDED_DOMINANT,
    }:
        if "dominant" in sf:
            return .88
    if p.kind is ReharmonizationKind.MODAL_INTERCHANGE:
        return .62
    if p.kind in {
        ReharmonizationKind.INTERPOLATION,
        ReharmonizationKind.CHROMATIC_APPROACH,
        ReharmonizationKind.DIMINISHED_APPROACH,
    }:
        return .52
    return .35


def assess_reharmonization(p: ReharmonizationProposal) -> ReharmonizationAssessment:
    p.validate()
    reasons: list[str] = []
    accepted: list[ContinuityAxis] = []

    target = _target_preservation(p)
    function = _function_preservation(p)
    common = _common_tone_support(p.original.pitch_classes, p.substitute.pitch_classes)
    melody = _melody_compatibility(p.substitute)

    # Voice-leading is estimated semantically here; detailed note/voice scoring
    # remains in voice_leading.py when concrete voices are available.
    root_motion = _root_motion_support(p.original.root_pc, p.substitute.root_pc)
    voice = .55 * common + .45 * root_motion

    bass = .5
    if p.original.bass_pc is not None and p.substitute.bass_pc is not None:
        bass = _root_motion_support(p.original.bass_pc, p.substitute.bass_pc)

    modal = .0
    if p.kind is ReharmonizationKind.MODAL_INTERCHANGE:
        same_tonic = (
            p.original.root_pc is not None
            and p.substitute.root_pc is not None
            and p.original.root_pc == p.substitute.root_pc
        )
        modal = .72 if same_tonic else .48

    narrative = min(1.0, .55 + max(-.35, min(.35, p.tension_delta)) * .8)

    checks = (
        (ContinuityAxis.TARGET_PRESERVATION, target, .60, "target preserved"),
        (ContinuityAxis.FUNCTION_PRESERVATION, function, .65, "function preserved"),
        (ContinuityAxis.COMMON_TONE, common, .34, "common tones connect sonorities"),
        (ContinuityAxis.VOICE_LEADING, voice, .55, "voice-leading path is plausible"),
        (ContinuityAxis.BASS_LOGIC, bass, .60, "bass motion supports transition"),
        (ContinuityAxis.MELODY_COMPATIBILITY, melody, .65, "melody remains compatible"),
        (ContinuityAxis.MODAL_BORROWING, modal, .55, "modal-borrowing relation is audible"),
        (ContinuityAxis.NARRATIVE_TENSION, narrative, .55, "tension change fits narrative"),
    )
    for axis, value, threshold, reason in checks:
        if value >= threshold:
            accepted.append(axis)
            reasons.append(reason)

    # User-supplied / upstream-known axes add modest confidence, but cannot
    # replace all musical continuity evidence.
    declared_bonus = .025 * len(p.axes & frozenset(accepted))
    continuity = (
        .23 * target
        + .16 * function
        + .13 * common
        + .16 * voice
        + .09 * bass
        + .13 * melody
        + .05 * modal
        + .05 * narrative
        + declared_bonus
    )
    continuity = min(1.0, max(0.0, continuity))

    # Risk means "how much explanatory continuity is missing", not "illegal".
    risk = max(0.0, 1.0 - continuity)
    if target < .35:
        risk = min(1.0, risk + .12)
        reasons.append("target relation is weak or redirected")
    if melody < .35:
        risk = min(1.0, risk + .12)
        reasons.append("melody compatibility is weak")
    if p.kind is ReharmonizationKind.NONFUNCTIONAL_COLOR and not accepted:
        risk = min(1.0, risk + .10)
        reasons.append("nonfunctional color lacks an explicit continuity mechanism")

    return ReharmonizationAssessment(
        continuity,
        target,
        function,
        common,
        voice,
        bass,
        melody,
        modal,
        narrative,
        risk,
        tuple(accepted),
        tuple(reasons),
    )


def tritone_substitute_root(dominant_root_pc: int) -> int:
    if not 0 <= dominant_root_pc <= 11:
        raise ValueError("dominant_root_pc must be in 0..11")
    return (dominant_root_pc + 6) % 12


def make_substitute_dominant_proposal(
    *,
    proposal_id: str,
    dominant_root_pc: int,
    target_root_pc: int,
    original_pitch_classes: Sequence[int] = (),
    substitute_pitch_classes: Sequence[int] = (),
    melody_pcs: Sequence[int] = (),
    provenance: Sequence[str] = (),
) -> ReharmonizationProposal:
    sub_root = tritone_substitute_root(dominant_root_pc)
    return ReharmonizationProposal(
        proposal_id=proposal_id,
        kind=ReharmonizationKind.SUBSTITUTE_DOMINANT,
        original=HarmonicSnapshot(
            root_pc=dominant_root_pc,
            pitch_classes=frozenset(original_pitch_classes),
            function="dominant",
            target_root_pc=target_root_pc,
            melody_pcs=frozenset(melody_pcs),
        ),
        substitute=HarmonicSnapshot(
            root_pc=sub_root,
            pitch_classes=frozenset(substitute_pitch_classes),
            function="substitute_dominant",
            target_root_pc=target_root_pc,
            melody_pcs=frozenset(melody_pcs),
        ),
        axes=frozenset({
            ContinuityAxis.TARGET_PRESERVATION,
            ContinuityAxis.FUNCTION_PRESERVATION,
            ContinuityAxis.VOICE_LEADING,
        }),
        intended_target_pc=target_root_pc,
        confidence=.9,
        provenance=tuple(provenance),
        note="Tritone-related dominant substitution preserving the intended destination.",
    )
