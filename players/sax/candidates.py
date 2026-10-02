"""Sax candidate-source and immediate-event generation.

Legend memory, Shared Scale/Linear intelligence, score context, ensemble
interaction, and sax physical feasibility all bias the *current* event only.
No function here schedules a future phrase.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.harmony.jazz_harmony_core import HarmonicFrame
from music_intelligence.harmony.scale_linear_core import (
    LinearDirection,
    LinearRouteKind,
    build_linear_connection_affordances,
)
from music_intelligence.legends import LegendDomain, VocabularyUseType
from music_intelligence.reasoning.legend_style_core import CandidateEvent

from .interaction import SaxInteractionDecision
from .legend_context import SaxLegendContext, SaxMemoryIntention
from .physical import SaxPhysicalAssessment, SaxPhysicalConstraints, assess_sax_transition
from .score_context import SaxScoreActivity, SaxScorePolicyContext


@dataclass(frozen=True)
class SaxLegendCandidateContext:
    domain: LegendDomain
    harmony_context: str = ""
    harmonic_function: str = ""
    local_key: str = ""
    phrase_position: str = ""
    active_tags: tuple[str, ...] = ()
    allowed_uses: frozenset[VocabularyUseType] = frozenset(VocabularyUseType)
    vocabulary_limit: int = 8


@dataclass(frozen=True)
class SaxLegendCandidateMaterial:
    source_family: str
    domain: LegendDomain
    feature: str = ""
    vocabulary_id: str = ""
    use_type: VocabularyUseType | None = None
    score_bias: float = 0.0
    confidence: float = 1.0
    recent_usage_count: int = 0
    reasons: tuple[str, ...] = ()


def collect_legend_candidate_material(
    legend: SaxLegendContext,
    context: SaxLegendCandidateContext,
) -> tuple[SaxLegendCandidateMaterial, ...]:
    out: list[SaxLegendCandidateMaterial] = []

    for tendency in legend.tendencies(
        domain=context.domain,
        active_tags=context.active_tags,
    ):
        bias = legend.feature_bias(
            domain=context.domain,
            feature=tendency.feature,
            active_tags=context.active_tags,
        )
        out.append(SaxLegendCandidateMaterial(
            source_family="legend_prior",
            domain=context.domain,
            feature=tendency.feature,
            score_bias=bias,
            confidence=tendency.confidence,
            reasons=(tendency.tendency_id,),
        ))

    memories = legend.vocabulary(
        domain=context.domain,
        harmony_context=context.harmony_context,
        harmonic_function=context.harmonic_function,
        local_key=context.local_key,
        phrase_position=context.phrase_position,
        context_tags=frozenset(context.active_tags),
        allowed_uses=context.allowed_uses,
        limit=context.vocabulary_limit,
    )
    for item in memories:
        supported_uses = tuple(
            use for use in context.allowed_uses
            if use in item.candidate_uses
        )
        for use in supported_uses:
            repetition_pressure = min(.25, .04 * item.recent_usage_count)
            out.append(SaxLegendCandidateMaterial(
                source_family="legend_vocabulary",
                domain=context.domain,
                vocabulary_id=item.vocabulary_id,
                use_type=use,
                score_bias=item.confidence - repetition_pressure,
                confidence=item.confidence,
                recent_usage_count=item.recent_usage_count,
                reasons=(item.source_id, f"use:{use.value}"),
            ))

    return tuple(sorted(
        out,
        key=lambda x: (x.score_bias, x.confidence, x.vocabulary_id, x.feature),
        reverse=True,
    ))


@dataclass(frozen=True)
class SaxImmediateContext:
    previous_pitch_midi: int | None = None
    register_low_midi: int = 50
    register_high_midi: int = 94
    duration_beats: float = .5
    target_pitch_classes: frozenset[int] = frozenset()
    local_key_pitch_classes: frozenset[int] = frozenset()
    allow_improvisation: bool = False
    written_pitch_midi: int | None = None
    written_duration_beats: float | None = None
    notes_since_breath: int = 0
    beats_since_breath: float = 0.0
    physical_constraints: SaxPhysicalConstraints | None = None
    score_policy: SaxScorePolicyContext | None = None
    interaction: SaxInteractionDecision | None = None
    legend_materials: tuple[SaxLegendCandidateMaterial, ...] = ()
    memory_intention: SaxMemoryIntention | None = None
    max_candidates: int = 24

    def validate(self) -> None:
        if not 0 <= self.register_low_midi <= self.register_high_midi <= 127:
            raise ValueError("invalid sax register")
        if self.previous_pitch_midi is not None and not 0 <= self.previous_pitch_midi <= 127:
            raise ValueError("previous_pitch_midi must be MIDI")
        if self.written_pitch_midi is not None and not 0 <= self.written_pitch_midi <= 127:
            raise ValueError("written_pitch_midi must be MIDI")
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")
        if self.written_duration_beats is not None and self.written_duration_beats <= 0:
            raise ValueError("written_duration_beats must be positive")
        if any(not 0 <= pc <= 11 for pc in self.local_key_pitch_classes):
            raise ValueError("local key pitch classes must be in 0..11")
        if any(not 0 <= pc <= 11 for pc in self.target_pitch_classes):
            raise ValueError("target pitch classes must be in 0..11")
        if self.max_candidates <= 0:
            raise ValueError("max_candidates must be positive")


@dataclass(frozen=True)
class SaxActionCandidate:
    event: CandidateEvent
    route: LinearRouteKind | None
    score: float
    physical: SaxPhysicalAssessment | None = None
    memory_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


def _pitch_realizations(pc: int, ctx: SaxImmediateContext) -> tuple[int, ...]:
    pitches = [
        p for p in range(ctx.register_low_midi, ctx.register_high_midi + 1)
        if p % 12 == pc % 12
    ]
    if not pitches:
        return ()
    target = ctx.previous_pitch_midi
    if target is None:
        target = (ctx.register_low_midi + ctx.register_high_midi) / 2
    ordered = sorted(pitches, key=lambda p: (abs(p - target), p))
    return tuple(ordered[:2])


def _route_tags(route: LinearRouteKind) -> frozenset[str]:
    table = {
        LinearRouteKind.CHORDAL: {"chord_tone", "structural"},
        LinearRouteKind.DIATONIC_PASSING: {"passing", "voice_leading"},
        LinearRouteKind.CHROMATIC_PASSING: {"chromatic", "passing"},
        LinearRouteKind.NEIGHBOR: {"neighbor"},
        LinearRouteKind.ENCLOSURE: {"enclosure", "directed_target"},
        LinearRouteKind.SCALE_FRAGMENT: {"scale_fragment", "color_tone"},
        LinearRouteKind.ARPEGGIO_FRAGMENT: {"arpeggio_fragment", "chord_tone"},
        LinearRouteKind.COMMON_TONE: {"common_tone", "stable_harmony"},
        LinearRouteKind.APPROACH: {"close_approach", "directed_target"},
        LinearRouteKind.ANTICIPATION: {"anticipation", "future_harmony"},
    }
    return frozenset(table.get(route, set()))


def _physical(
    pitch: int,
    ctx: SaxImmediateContext,
) -> SaxPhysicalAssessment | None:
    if ctx.physical_constraints is None:
        return None
    return assess_sax_transition(
        pitch_midi=pitch,
        previous_pitch_midi=ctx.previous_pitch_midi,
        notes_since_breath=ctx.notes_since_breath,
        beats_since_breath=ctx.beats_since_breath,
        constraints=ctx.physical_constraints,
    )


def _memory_direction_score(pitch: int, ctx: SaxImmediateContext) -> float:
    intention = ctx.memory_intention
    previous = ctx.previous_pitch_midi
    if intention is None or previous is None:
        return 0.0
    direction = intention.direction.lower()
    delta = pitch - previous
    if direction in {"rising", "ascending", "up"}:
        return .05 if delta > 0 else -.025 if delta < 0 else 0.0
    if direction in {"falling", "descending", "down"}:
        return .05 if delta < 0 else -.025 if delta > 0 else 0.0
    if direction in {"stable", "level"}:
        return .035 if abs(delta) <= 2 else -.015
    return 0.0


def _score_context_bias(
    route: LinearRouteKind,
    ctx: SaxImmediateContext,
) -> float:
    score = ctx.score_policy
    if score is None:
        return 0.0
    value = 0.0
    if "bebop" in score.style_tags and route in {
        LinearRouteKind.DIATONIC_PASSING,
        LinearRouteKind.APPROACH,
        LinearRouteKind.ENCLOSURE,
        LinearRouteKind.ARPEGGIO_FRAGMENT,
    }:
        value += .045
    if score.phrase_end_bias > 0:
        if route in {LinearRouteKind.CHORDAL, LinearRouteKind.COMMON_TONE, LinearRouteKind.ANTICIPATION}:
            value += .06 * score.phrase_end_bias
        elif route in {LinearRouteKind.NEIGHBOR, LinearRouteKind.ENCLOSURE}:
            value -= .025 * score.phrase_end_bias
    if score.transition_bias > 0 and route in {LinearRouteKind.CHORDAL, LinearRouteKind.COMMON_TONE}:
        value += .04 * score.transition_bias
    return value


def _legend_bias(
    *,
    tags: frozenset[str],
    ctx: SaxImmediateContext,
    duration_beats: float,
) -> tuple[float, tuple[str, ...], tuple[str, ...]]:
    features = set(tags)
    if (
        ctx.score_policy is not None
        and ctx.score_policy.phrase_end_bias > 0
        and duration_beats >= .75
    ):
        features.add("structural_terminal_long_tone")

    value = 0.0
    reasons: list[str] = []
    memory_ids: list[str] = []
    seen_features: set[str] = set()

    for material in ctx.legend_materials:
        if material.source_family == "legend_prior":
            if material.feature in features and material.feature not in seen_features:
                value += material.score_bias
                seen_features.add(material.feature)
                reasons.append(f"legend prior:{material.feature}")
            continue

        intention = ctx.memory_intention
        if intention is None or material.vocabulary_id not in intention.active_vocabulary_ids:
            continue
        if material.use_type is not intention.use_type:
            continue

        # Literal/transposed quotation needs an actual extracted note payload.
        # Until that payload is supplied, do not pretend a freshly generated
        # pitch is the quoted lick. Transformative/hybrid memory may still bias
        # the generated current event.
        if material.use_type in {
            VocabularyUseType.HYBRID_COMPOSITION,
            VocabularyUseType.ABSTRACTED_PATTERN,
            VocabularyUseType.ADAPTED_LICK,
            VocabularyUseType.FRAGMENT_RECALL,
        }:
            value += .045 * material.confidence
            memory_ids.append(material.vocabulary_id)
            reasons.append(f"active legend memory:{material.vocabulary_id}")

    return value, tuple(dict.fromkeys(memory_ids)), tuple(reasons)


def _written_candidate(ctx: SaxImmediateContext) -> tuple[SaxActionCandidate, ...]:
    score = ctx.score_policy
    if score is None or score.activity not in {
        SaxScoreActivity.HEAD_WRITTEN,
        SaxScoreActivity.WRITTEN_SOLO,
        SaxScoreActivity.WRITTEN_PART,
    }:
        return ()
    if ctx.written_pitch_midi is None:
        return ()

    physical = _physical(ctx.written_pitch_midi, ctx)
    if physical is not None and not physical.feasible:
        return ()

    duration = ctx.written_duration_beats or ctx.duration_beats
    penalty = 0.0
    reasons = ["explicit written score event"]
    if physical is not None:
        penalty = .18 * physical.transition_cost + .10 * physical.breath_pressure
        reasons.extend(physical.reasons)

    event = CandidateEvent(
        ctx.written_pitch_midi,
        duration,
        tags=frozenset({"written_material", score.activity.value}),
        source_family="score_written",
    )
    return (SaxActionCandidate(
        event=event,
        route=None,
        score=1.0 - penalty,
        physical=physical,
        reasons=tuple(reasons),
    ),)


def _breath_pressure(ctx: SaxImmediateContext) -> float:
    c = ctx.physical_constraints
    if c is None:
        return 0.0
    c.validate()
    return min(1.0, max(
        ctx.notes_since_breath / c.max_notes_since_breath,
        ctx.beats_since_breath / c.max_beats_since_breath,
    ))


def generate_immediate_sax_candidates(
    frame: HarmonicFrame,
    ctx: SaxImmediateContext,
) -> tuple[SaxActionCandidate, ...]:
    """Generate only the next sax event candidates, never a future line."""
    frame.validate()
    ctx.validate()

    if ctx.score_policy is not None and ctx.score_policy.activity in {
        SaxScoreActivity.HEAD_WRITTEN,
        SaxScoreActivity.WRITTEN_SOLO,
        SaxScoreActivity.WRITTEN_PART,
    }:
        return _written_candidate(ctx)

    explicit_open = (
        ctx.score_policy is not None
        and ctx.score_policy.activity is SaxScoreActivity.OPEN_SOLO
    )
    if not (explicit_open or ctx.allow_improvisation):
        return ()

    current_pc = (
        ctx.previous_pitch_midi % 12
        if ctx.previous_pitch_midi is not None
        else None
    )
    routes = build_linear_connection_affordances(
        frame,
        current_pitch_class=current_pc,
        target_pitch_classes=ctx.target_pitch_classes,
        local_key_pitch_classes=ctx.local_key_pitch_classes,
    )

    out: list[SaxActionCandidate] = []
    seen: set[tuple[LinearRouteKind, int]] = set()

    for route in routes:
        tags = _route_tags(route.route)
        for pc in sorted(route.immediate_pitch_classes):
            for pitch in _pitch_realizations_for_route(pc, route.direction, ctx):
                key = (route.route, pitch)
                if key in seen:
                    continue
                seen.add(key)

                physical = _physical(pitch, ctx)
                if physical is not None and not physical.feasible:
                    continue

                score = route.weight
                reasons = [f"shared linear route:{route.route.value}"]
                if ctx.previous_pitch_midi is not None:
                    interval = abs(pitch - ctx.previous_pitch_midi)
                    score += .045 * (1.0 - min(interval, 12) / 12.0)

                score += _memory_direction_score(pitch, ctx)
                score += _score_context_bias(route.route, ctx)

                if physical is not None:
                    score -= .18 * physical.transition_cost
                    score -= .10 * physical.breath_pressure
                    reasons.extend(physical.reasons)

                if ctx.interaction is not None:
                    score -= .08 * ctx.interaction.rest_bias
                    if (
                        ctx.interaction.answer_bias > 0
                        and route.route in {
                            LinearRouteKind.DIATONIC_PASSING,
                            LinearRouteKind.APPROACH,
                            LinearRouteKind.ANTICIPATION,
                            LinearRouteKind.COMMON_TONE,
                        }
                    ):
                        score += .05 * ctx.interaction.answer_bias
                        reasons.append("supports sax answer role")
                    if (
                        ctx.interaction.lead_bias > 0
                        and route.route in {
                            LinearRouteKind.ENCLOSURE,
                            LinearRouteKind.SCALE_FRAGMENT,
                            LinearRouteKind.ARPEGGIO_FRAGMENT,
                        }
                    ):
                        score += .035 * ctx.interaction.lead_bias

                legend_delta, memory_ids, legend_reasons = _legend_bias(
                    tags=tags,
                    ctx=ctx,
                    duration_beats=ctx.duration_beats,
                )
                score += legend_delta
                reasons.extend(legend_reasons)

                event_tags = set(tags)
                event_tags.update(f"legend_memory:{x}" for x in memory_ids)
                if ctx.score_policy is not None:
                    event_tags.update(f"style:{x}" for x in ctx.score_policy.style_tags)

                out.append(SaxActionCandidate(
                    event=CandidateEvent(
                        pitch,
                        ctx.duration_beats,
                        tags=frozenset(event_tags),
                        source_family=(
                            "hybrid_memory"
                            if memory_ids else "shared_linear"
                        ),
                    ),
                    route=route.route,
                    score=score,
                    physical=physical,
                    memory_ids=memory_ids,
                    reasons=tuple(reasons),
                ))

    rest_bias = 0.0
    rest_reasons: list[str] = []
    if ctx.score_policy is not None:
        rest_bias += ctx.score_policy.space_bias
        rest_bias += .12 * ctx.score_policy.phrase_end_bias
        rest_bias += .06 * ctx.score_policy.transition_bias
        if ctx.score_policy.phrase_boundary_after:
            rest_reasons.append("explicit score phrase boundary supports space")
    if ctx.interaction is not None:
        rest_bias += ctx.interaction.rest_bias
        rest_reasons.extend(ctx.interaction.reasons)
    breath = _breath_pressure(ctx)
    if breath >= .75:
        rest_bias += .18 * breath
        rest_reasons.append("breath pressure supports immediate space")

    if rest_bias > 0:
        rest_tags = frozenset({"rest", "ensemble_space"})
        legend_delta, memory_ids, legend_reasons = _legend_bias(
            tags=rest_tags,
            ctx=ctx,
            duration_beats=max(.5, ctx.duration_beats),
        )
        rest_reasons.extend(legend_reasons)
        rest_duration = 1.0 if (
            ctx.score_policy is not None and ctx.score_policy.phrase_boundary_after
        ) else max(.5, ctx.duration_beats)
        out.append(SaxActionCandidate(
            event=CandidateEvent(
                None,
                rest_duration,
                tags=rest_tags,
                source_family="generated_space",
            ),
            route=None,
            score=.02 + rest_bias + legend_delta,
            memory_ids=memory_ids,
            reasons=tuple(rest_reasons),
        ))

    ranked = sorted(
        out,
        key=lambda x: (x.score, x.event.pitch_midi is not None),
        reverse=True,
    )

    # Preserve route diversity before filling the remaining beam by score.
    # Otherwise a large high-scoring route family (for example APPROACH) can
    # crowd future-harmony ANTICIPATION or another legitimate route completely
    # out of the immediate candidate set.
    selected: list[SaxActionCandidate] = []
    selected_keys: set[tuple[LinearRouteKind | None, int | None, str]] = set()
    route_seen: set[LinearRouteKind | None] = set()
    for item in ranked:
        if item.route in route_seen:
            continue
        route_seen.add(item.route)
        key = (item.route, item.event.pitch_midi, item.event.source_family)
        selected.append(item)
        selected_keys.add(key)
        if len(selected) >= ctx.max_candidates:
            return tuple(selected)

    for item in ranked:
        key = (item.route, item.event.pitch_midi, item.event.source_family)
        if key in selected_keys:
            continue
        selected.append(item)
        selected_keys.add(key)
        if len(selected) >= ctx.max_candidates:
            break
    return tuple(selected)


def _pitch_realizations_for_route(
    pc: int,
    direction: LinearDirection,
    ctx: SaxImmediateContext,
) -> tuple[int, ...]:
    options = _pitch_realizations(pc, ctx)
    if ctx.previous_pitch_midi is None or direction is LinearDirection.EITHER:
        return options
    if direction is LinearDirection.ASCENDING:
        preferred = tuple(x for x in options if x >= ctx.previous_pitch_midi)
        return preferred or options
    if direction is LinearDirection.DESCENDING:
        preferred = tuple(x for x in options if x <= ctx.previous_pitch_midi)
        return preferred or options
    if direction is LinearDirection.STABLE:
        return options[:1]
    return options
