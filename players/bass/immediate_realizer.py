"""Bass-specific immediate-action realization.

Consumes Shared Core harmony/voice-leading plus bass Performance Grammar.
No separate bass harmony engine and no frozen future line.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.harmony.jazz_harmony_core import HarmonicFrame, build_basic_affordances
from music_intelligence.harmony.scale_linear_core import (
    LinearRouteKind,
    build_linear_connection_affordances,
)
from music_intelligence.harmony.voice_leading import (
    TargetRole,
    VoiceLeadingContext,
    VoiceRole,
    VoiceState,
    assess_voice_leading,
)
from music_intelligence.reasoning.legend_style_core import CandidateEvent

from .interaction_grammar import (
    BassInteractionDecision,
    BassInteractionIntent,
)
from .performance_grammar import (
    BassGrammarContext,
    BassGrammarDecision,
    MotionStrategy,
    RegisterIntent,
    TargetStrategy,
    evaluate_bass_grammar,
)
from .performance_expression import BassExpressionProfile, realize_bass_expression
from .phrase_intent import (
    BassPhraseDirection,
    BassPhraseIntent,
    BassPhraseIntentKind,
)
from .performance_memory import BassPerformanceSnapshot
from .scorebook_evidence import (
    BassScoreEvidenceDirective,
    evidence_candidate_score,
)


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
    DIATONIC_PASSING = "diatonic_passing"
    NEIGHBOR = "neighbor"
    SCALE_COLOR = "scale_color"
    PEDAL = "pedal"


@dataclass(frozen=True)
class BassContext:
    mode: BassMode = BassMode.WALKING
    beat_in_measure: float = 0.0
    meter_numerator: int = 4
    previous_pitch_midi: int | None = None
    previous_motion_semitones: int | None = None
    register_low_midi: int = 28
    register_high_midi: int = 55
    register_intent: RegisterIntent = RegisterIntent.STABLE
    repeated_note_tolerance: float = 0.35
    stepwise_preference: float = 0.45
    contour_reversal_pressure: float = 0.45
    ensemble_activity: float = 0.5
    memory_snapshot: BassPerformanceSnapshot = BassPerformanceSnapshot()
    interaction_decision: BassInteractionDecision | None = None
    local_key_pitch_classes: frozenset[int] = frozenset()
    score_evidence: BassScoreEvidenceDirective = BassScoreEvidenceDirective()
    phrase_intent: BassPhraseIntent = BassPhraseIntent(BassPhraseIntentKind.GROUND)

    def validate(self) -> None:
        if self.meter_numerator <= 0:
            raise ValueError("meter_numerator must be positive")
        if not 0.0 <= self.beat_in_measure < self.meter_numerator:
            raise ValueError("beat_in_measure must fall inside the current measure")
        if not 0 <= self.register_low_midi <= self.register_high_midi <= 127:
            raise ValueError("invalid bass register")
        if self.previous_pitch_midi is not None and not 0 <= self.previous_pitch_midi <= 127:
            raise ValueError("previous_pitch_midi must be in MIDI range")
        if any(not 0 <= pc <= 11 for pc in self.local_key_pitch_classes):
            raise ValueError("local_key_pitch_classes must be in 0..11")
        for name, value in (
            ("repeated_note_tolerance", self.repeated_note_tolerance),
            ("stepwise_preference", self.stepwise_preference),
            ("contour_reversal_pressure", self.contour_reversal_pressure),
            ("ensemble_activity", self.ensemble_activity),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


@dataclass(frozen=True)
class BassActionCandidate:
    event: CandidateEvent
    harmonic_role: BassHarmonicRole
    target_pitch_class: int
    score: float
    grammar: BassGrammarDecision
    expression: BassExpressionProfile
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


def _pitch_realizations_for_pc(pc: int, ctx: BassContext) -> tuple[int, ...]:
    options = [
        p for p in range(ctx.register_low_midi, ctx.register_high_midi + 1)
        if p % 12 == pc % 12
    ]
    if not options:
        raise ValueError("register contains no realization for requested pitch class")

    target = ctx.previous_pitch_midi
    if target is None:
        target = (ctx.register_low_midi + ctx.register_high_midi) / 2
        ordered = sorted(options, key=lambda p: (abs(p - target), p))
        # Pedal is a single sustained/recurring anchor; octave alternatives
        # belong to later pedal-register planning, not immediate branching.
        if ctx.mode is BassMode.PEDAL:
            return (ordered[0],)
        return tuple(ordered[:2])

    # Keep the nearest realization and, when available, one on the opposite side.
    nearest = min(options, key=lambda p: (abs(p - target), p))
    if ctx.mode is BassMode.PEDAL:
        return (nearest,)
    below = [p for p in options if p < target]
    above = [p for p in options if p > target]
    selected = [nearest]
    if below:
        selected.append(max(below))
    if above:
        selected.append(min(above))

    # Preserve order while removing duplicates.
    return tuple(dict.fromkeys(selected))


def _duration_for_mode(mode: BassMode) -> float:
    return 2.0 if mode is BassMode.TWO_FEEL else 1.0


def _voice_role_for(candidate: BassHarmonicRole) -> TargetRole:
    if candidate in {BassHarmonicRole.ROOT, BassHarmonicRole.PEDAL}:
        return TargetRole.ROOT
    if candidate is BassHarmonicRole.FIFTH:
        return TargetRole.FIFTH
    if candidate in {BassHarmonicRole.CHROMATIC_APPROACH, BassHarmonicRole.ANTICIPATION}:
        return TargetRole.STRUCTURAL
    if candidate in {
        BassHarmonicRole.DIATONIC_PASSING,
        BassHarmonicRole.NEIGHBOR,
        BassHarmonicRole.SCALE_COLOR,
    }:
        return TargetRole.TENSION
    return TargetRole.UNKNOWN


def _grammar_mapping(role: BassHarmonicRole) -> tuple[MotionStrategy, TargetStrategy]:
    if role is BassHarmonicRole.ROOT:
        return MotionStrategy.CHORDAL, TargetStrategy.CURRENT_ROOT
    if role in {BassHarmonicRole.FIFTH, BassHarmonicRole.CHORD_TONE}:
        return MotionStrategy.CHORDAL, TargetStrategy.CURRENT_CHORD_MEMBER
    if role is BassHarmonicRole.CHROMATIC_APPROACH:
        return MotionStrategy.CHROMATIC_APPROACH, TargetStrategy.NEXT_ROOT
    if role is BassHarmonicRole.ANTICIPATION:
        return MotionStrategy.DIRECT_ANTICIPATION, TargetStrategy.NEXT_ROOT
    if role in {
        BassHarmonicRole.DIATONIC_PASSING,
        BassHarmonicRole.NEIGHBOR,
        BassHarmonicRole.SCALE_COLOR,
    }:
        return MotionStrategy.SHARED_SCALE_OR_COLOR, TargetStrategy.NONE
    if role is BassHarmonicRole.PEDAL:
        return MotionStrategy.PEDAL, TargetStrategy.CURRENT_ROOT
    raise ValueError(f"unsupported bass harmonic role: {role}")


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


def _grammar_context(ctx: BassContext) -> BassGrammarContext:
    return BassGrammarContext(
        beat_in_measure=ctx.beat_in_measure,
        meter_numerator=ctx.meter_numerator,
        walking=ctx.mode is BassMode.WALKING,
        two_feel=ctx.mode is BassMode.TWO_FEEL,
        pedal=ctx.mode is BassMode.PEDAL,
        previous_pitch_midi=ctx.previous_pitch_midi,
        previous_motion_semitones=ctx.previous_motion_semitones,
        register_intent=ctx.register_intent,
        repeated_note_tolerance=ctx.repeated_note_tolerance,
        stepwise_preference=ctx.stepwise_preference,
        contour_reversal_pressure=ctx.contour_reversal_pressure,
        ensemble_activity=ctx.ensemble_activity,
    )


def _interaction_memory_score(
    *,
    ctx: BassContext,
    pitch: int,
    role: BassHarmonicRole,
) -> tuple[float, tuple[str, ...]]:
    """Score one current candidate using bass-local causal memory/intent.

    No future note sequence is stored. The function only asks whether this
    immediate candidate supports or violates the current bass role and recent
    performance trajectory.
    """
    score = 0.0
    reasons: list[str] = []
    memory = ctx.memory_snapshot
    decision = ctx.interaction_decision

    previous = ctx.previous_pitch_midi
    if previous is None:
        previous = memory.previous_pitch_midi
    delta = pitch - previous if previous is not None else None

    if memory.consecutive_step_count >= 3 and delta is not None and 0 < abs(delta) <= 2:
        score -= .08
        reasons.append("stepwise momentum saturation")

    # Walking should not repeat the same role-grid every bar. If the candidate
    # recreates the role heard at the same metric slot one bar ago, apply a
    # modest diversity pressure. This is softer than randomization: harmony,
    # voice-leading and interaction may still justify the repetition.
    if ctx.mode is BassMode.WALKING and len(memory.recent_harmonic_roles) >= 4:
        previous_same_slot = memory.recent_harmonic_roles[-4]
        if role.value == previous_same_slot:
            score -= .055
            reasons.append("walking role-pattern repetition pressure")
        if len(memory.recent_harmonic_roles) >= 8:
            last4 = memory.recent_harmonic_roles[-4:]
            prev4 = memory.recent_harmonic_roles[-8:-4]
            if last4 == prev4 and role.value == previous_same_slot:
                score -= .045
                reasons.append("repeated bar-level walking template")

        directed = {"chromatic_approach", "anticipation"}
        recent_directed = sum(
            x in directed for x in memory.recent_harmonic_roles[-8:]
        )
        if role.value in directed and recent_directed >= 2:
            score -= .10
            reasons.append("recent approach budget already used")

    if (
        memory.consecutive_direction_count >= 3
        and memory.previous_interval_semitones not in (None, 0)
        and delta not in (None, 0)
    ):
        same_direction = (memory.previous_interval_semitones > 0) == (delta > 0)
        if same_direction:
            score -= .08
            reasons.append("prolonged same-direction contour")
        else:
            score += .05
            reasons.append("contour recovery")
    elif (
        ctx.mode is BassMode.WALKING
        and memory.consecutive_direction_count >= 2
        and memory.previous_interval_semitones not in (None, 0)
        and delta not in (None, 0)
    ):
        same_direction = (memory.previous_interval_semitones > 0) == (delta > 0)
        if same_direction:
            score -= .025
            reasons.append("soft contour-fatigue pressure")

    if decision is not None:
        intent = decision.intent
        stable_roles = {
            BassHarmonicRole.ROOT,
            BassHarmonicRole.FIFTH,
            BassHarmonicRole.CHORD_TONE,
            BassHarmonicRole.PEDAL,
        }
        directed_roles = {
            BassHarmonicRole.CHROMATIC_APPROACH,
            BassHarmonicRole.ANTICIPATION,
            BassHarmonicRole.DIATONIC_PASSING,
            BassHarmonicRole.NEIGHBOR,
            BassHarmonicRole.SCALE_COLOR,
        }

        if intent in {
            BassInteractionIntent.ANCHOR,
            BassInteractionIntent.HOLD,
            BassInteractionIntent.YIELD,
            BassInteractionIntent.RESET,
            BassInteractionIntent.RELEASE,
        }:
            if role is BassHarmonicRole.ROOT:
                score += .07
                reasons.append(f"{intent.value} favors harmonic floor")
            elif role in directed_roles:
                score -= .05
                reasons.append(f"{intent.value} reduces decorative direction")

        elif intent in {
            BassInteractionIntent.CONNECT,
            BassInteractionIntent.PROPEL,
            BassInteractionIntent.ANSWER,
            BassInteractionIntent.FILL,
            BassInteractionIntent.BUILD,
        }:
            if role in directed_roles:
                score += .06
                reasons.append(f"{intent.value} supports directional connection")
            elif role in stable_roles:
                score += .01

        if decision.complexity_delta < 0 and role in directed_roles:
            score += .08 * decision.complexity_delta
            reasons.append("interaction complexity reduction")
        elif decision.complexity_delta > 0 and role in directed_roles:
            score += .05 * decision.complexity_delta

        if (
            decision.register_recovery > 0
            and delta not in (None, 0)
            and memory.phrase_register_slope != 0
        ):
            wants_down = memory.phrase_register_slope > 0
            recovers = (delta < 0) if wants_down else (delta > 0)
            amount = .10 * decision.register_recovery
            score += amount if recovers else -amount
            reasons.append(
                "supports register recovery" if recovers
                else "extends register excursion"
            )

    return score, tuple(reasons)


def _phrase_intent_score(
    *,
    ctx: BassContext,
    pitch: int,
    role: BassHarmonicRole,
) -> tuple[float, tuple[str, ...]]:
    """Score one immediate candidate against the current multi-event phrase plan."""
    intent = ctx.phrase_intent
    score = 0.0
    reasons: list[str] = []

    structural = {
        BassHarmonicRole.ROOT,
        BassHarmonicRole.FIFTH,
        BassHarmonicRole.CHORD_TONE,
        BassHarmonicRole.PEDAL,
    }
    connective = {
        BassHarmonicRole.DIATONIC_PASSING,
        BassHarmonicRole.CHROMATIC_APPROACH,
        BassHarmonicRole.ANTICIPATION,
        BassHarmonicRole.NEIGHBOR,
        BassHarmonicRole.SCALE_COLOR,
    }

    if intent.kind in {
        BassPhraseIntentKind.GROUND,
        BassPhraseIntentKind.RELEASE,
        BassPhraseIntentKind.RESET,
    }:
        if role is BassHarmonicRole.ROOT:
            score += .055
            reasons.append(f"phrase {intent.kind.value} favors clear bass orientation")
        elif role is BassHarmonicRole.FIFTH:
            score += .025
        elif role in connective:
            score -= .045
            reasons.append(f"phrase {intent.kind.value} reduces information density")

    elif intent.kind is BassPhraseIntentKind.DEVELOP:
        if role in {
            BassHarmonicRole.DIATONIC_PASSING,
            BassHarmonicRole.CHORD_TONE,
            BassHarmonicRole.NEIGHBOR,
        }:
            score += .035
            reasons.append("phrase development supports connective variety")
        if role in {
            BassHarmonicRole.CHROMATIC_APPROACH,
            BassHarmonicRole.ANTICIPATION,
        }:
            score += .015

    elif intent.kind is BassPhraseIntentKind.BUILD:
        if role in connective:
            score += .055
            reasons.append("phrase build supports directional information")
        elif role is BassHarmonicRole.ROOT:
            score -= .015

    elif intent.kind is BassPhraseIntentKind.SUSTAIN:
        if role in structural:
            score += .018
        if role in {BassHarmonicRole.NEIGHBOR, BassHarmonicRole.SCALE_COLOR}:
            score -= .018

    previous = ctx.previous_pitch_midi
    if previous is not None and pitch != previous:
        delta = pitch - previous
        if intent.direction is BassPhraseDirection.RISE:
            score += .022 if delta > 0 else -.012
        elif intent.direction is BassPhraseDirection.FALL:
            score += .022 if delta < 0 else -.012
        elif intent.direction is BassPhraseDirection.RECOVER:
            slope = ctx.memory_snapshot.phrase_register_slope
            if slope > 0:
                score += .032 if delta < 0 else -.020
            elif slope < 0:
                score += .032 if delta > 0 else -.020

    return score, tuple(reasons)


def generate_immediate_bass_candidates(
    frame: HarmonicFrame,
    ctx: BassContext,
) -> tuple[BassActionCandidate, ...]:
    frame.validate()
    ctx.validate()
    build_basic_affordances(frame)

    root_pc = _active_root_pc(frame)
    if root_pc is None:
        return ()

    pcs = _active_pitch_classes(frame)
    duration = _duration_for_mode(ctx.mode)
    raw: list[tuple[int, BassHarmonicRole, float, tuple[str, ...]]] = []

    if ctx.mode is BassMode.PEDAL:
        raw.append((root_pc, BassHarmonicRole.PEDAL, 0.28, ("pedal anchor candidate",)))
    else:
        raw.append((root_pc, BassHarmonicRole.ROOT, 0.28, ("current harmonic anchor",)))

        fifth_pc = (root_pc + 7) % 12
        if not pcs or fifth_pc in pcs:
            raw.append((fifth_pc, BassHarmonicRole.FIFTH, 0.16,
                        ("shared evidence supports perfect-fifth option",)))

        # Two-feel should not be reduced to root-up-fifth. Other shared chord
        # members are legitimate immediate support choices.
        if ctx.mode in {BassMode.WALKING, BassMode.TWO_FEEL}:
            for pc in sorted(pcs):
                if pc in {root_pc, fifth_pc}:
                    continue
                base = 0.14 if ctx.mode is BassMode.WALKING else 0.035
                reason = (
                    "shared current-harmony pitch-class option"
                    if ctx.mode is BassMode.WALKING
                    else "two-feel non-root/fifth chord member kept as a low-priority color"
                )
                raw.append((pc, BassHarmonicRole.CHORD_TONE, base, (reason,)))

    next_root = frame.next_expected.root_pc if frame.next_expected is not None else None
    late_measure = ctx.beat_in_measure >= ctx.meter_numerator - 1.0
    if ctx.mode is BassMode.WALKING and next_root is not None and late_measure:
        raw.extend((
            ((next_root - 1) % 12, BassHarmonicRole.CHROMATIC_APPROACH, 0.16,
             ("chromatic lower approach to next expected root",)),
            ((next_root + 1) % 12, BassHarmonicRole.CHROMATIC_APPROACH, 0.13,
             ("chromatic upper approach to next expected root",)),
            (next_root, BassHarmonicRole.ANTICIPATION, 0.10,
             ("direct anticipation of next expected root",)),
        ))
    elif (
        ctx.mode is BassMode.TWO_FEEL
        and next_root is not None
        and ctx.beat_in_measure >= ctx.meter_numerator / 2.0
    ):
        raw.append((
            next_root,
            BassHarmonicRole.ANTICIPATION,
            0.08,
            ("second two-feel pulse may anticipate next expected root",),
        ))

    # Walking alone consumes Shared Scale/Linear Core in this slice.
    # Two-feel deliberately stays conservative after listening feedback.
    if ctx.mode is BassMode.WALKING:
        current_pc = (
            ctx.previous_pitch_midi % 12
            if ctx.previous_pitch_midi is not None
            else None
        )
        routes = build_linear_connection_affordances(
            frame,
            current_pitch_class=current_pc,
            local_key_pitch_classes=ctx.local_key_pitch_classes,
        )
        for route in routes:
            if route.route is LinearRouteKind.DIATONIC_PASSING:
                for pc in sorted(route.immediate_pitch_classes):
                    raw.append((
                        pc,
                        BassHarmonicRole.DIATONIC_PASSING,
                        0.095 + route.weight,
                        ("shared Core diatonic passing affordance",),
                    ))
            elif route.route is LinearRouteKind.NEIGHBOR and ctx.beat_in_measure in {1.0, 2.0}:
                for pc in sorted(route.immediate_pitch_classes):
                    raw.append((
                        pc,
                        BassHarmonicRole.NEIGHBOR,
                        0.02 + route.weight,
                        ("shared Core neighbor affordance",),
                    ))
            elif (
                route.route is LinearRouteKind.SCALE_FRAGMENT
                and ctx.local_key_pitch_classes
                and ctx.beat_in_measure in {1.0, 2.0}
            ):
                structural = _active_pitch_classes(frame)
                for pc in sorted(route.immediate_pitch_classes - structural):
                    raw.append((
                        pc,
                        BassHarmonicRole.SCALE_COLOR,
                        0.035 + route.weight,
                        ("shared Core contextual scale-color affordance",),
                    ))

    candidates: list[BassActionCandidate] = []
    seen: set[tuple[int, BassHarmonicRole, int]] = set()
    grammar_ctx = _grammar_context(ctx)

    for pc, role, base, reasons in raw:
        for pitch in _pitch_realizations_for_pc(pc, ctx):
            key = (pc % 12, role, pitch)
            if key in seen:
                continue
            seen.add(key)

            vl = _shared_voice_leading_score(ctx.previous_pitch_midi, pitch, role)
            motion_strategy, target_strategy = _grammar_mapping(role)
            grammar = evaluate_bass_grammar(
                ctx=grammar_ctx,
                candidate_pitch_midi=pitch,
                motion_strategy=motion_strategy,
                target_strategy=target_strategy,
            )

            motion_penalty = 0.0
            if ctx.previous_pitch_midi is not None:
                leap = abs(pitch - ctx.previous_pitch_midi)
                if leap > 7:
                    motion_penalty = 0.035 * (leap - 7)

            tags = {
                "bass", ctx.mode.value, role.value,
                grammar.metric_role.value, grammar.groove_relation.value,
                grammar.articulation_intent.value,
            }
            if role in {
                BassHarmonicRole.ROOT, BassHarmonicRole.FIFTH,
                BassHarmonicRole.CHORD_TONE, BassHarmonicRole.PEDAL,
            }:
                tags.add("chord_tone")
            if role in {
                BassHarmonicRole.CHROMATIC_APPROACH,
                BassHarmonicRole.ANTICIPATION,
                BassHarmonicRole.DIATONIC_PASSING,
                BassHarmonicRole.NEIGHBOR,
                BassHarmonicRole.SCALE_COLOR,
            }:
                tags.add("directed_target")
            if role in {
                BassHarmonicRole.DIATONIC_PASSING,
                BassHarmonicRole.NEIGHBOR,
                BassHarmonicRole.SCALE_COLOR,
            }:
                tags.add("shared_scale_linear")
            if role is BassHarmonicRole.ANTICIPATION:
                tags.add("anticipation")

            interaction_score, interaction_reasons = _interaction_memory_score(
                ctx=ctx,
                pitch=pitch,
                role=role,
            )
            evidence_score, evidence_reasons = evidence_candidate_score(
                ctx.score_evidence,
                mode=ctx.mode.value,
                harmonic_role=role.value,
                metric_role=grammar.metric_role.value,
            )
            phrase_score, phrase_reasons = _phrase_intent_score(
                ctx=ctx,
                pitch=pitch,
                role=role,
            )
            expression = realize_bass_expression(
                mode=ctx.mode.value,
                grammar=grammar,
                memory=ctx.memory_snapshot,
                interaction=ctx.interaction_decision,
                phrase_intent=ctx.phrase_intent,
            )
            score = (
                base
                + vl
                + grammar.score_delta
                + interaction_score
                + evidence_score
                + phrase_score
                - motion_penalty
            )
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
                grammar=grammar,
                expression=expression,
                reasons=(
                    reasons
                    + grammar.reasons
                    + interaction_reasons
                    + evidence_reasons
                    + phrase_reasons
                    + expression.reasons
                    + (f"shared voice-leading={vl:.3f}",)
                ),
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
