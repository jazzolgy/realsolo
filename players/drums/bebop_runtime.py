"""Bebop adapter over the generic online drummer.

The generic drum layer remains style-agnostic.  This module adds bebop-specific
interaction scoring while preserving the one-immediate-gesture runtime contract.
"""
from __future__ import annotations

from dataclasses import dataclass

from .bebop import (
    BassDrumIntent,
    BebopCompIntent,
    BebopInteractionDecision,
    BebopInteractionState,
    BebopPhraseMemory,
    SoloistEnergyProjection,
    choose_comp_intent,
    infer_bebop_interaction_state,
)
from .bebop_profile import BebopStyleProfile, DEFAULT_BEBOP_PROFILE
from .bass_coupling import (
    BassPulseProjection,
    coupling_score_adjustment,
    infer_bass_drums_coupling,
    project_bass_pulse,
)
from music_intelligence.reasoning.ensemble_state import EnsembleState
from .comping_phrase import (
    CompPhraseAction,
    SnarePhraseMemory,
    build_snare_phrase_candidates,
)
from .ride_continuity import (
    RideContinuityMemory,
    build_ride_candidates,
    score_ride_surface_gesture,
)
from .legend_adapter import DrumLegendProjection, legend_gesture_adjustment
from .model import (
    DrumGesture,
    DrumHit,
    DrummerRuntimeContext,
    DrummerSoftPlan,
    DrumVoice,
    GestureRole,
    Limb,
)
from .online_drummer import (
    DrummerPerformanceMemory,
    ScoredDrumGesture,
    build_immediate_candidates,
    score_gesture,
)


@dataclass(frozen=True)
class BebopRuntimeProjection:
    """Drummer-specific adapter for current ensemble evidence."""

    soloist: SoloistEnergyProjection
    phrase_memory: BebopPhraseMemory
    bass: BassPulseProjection | None = None
    ride_memory: RideContinuityMemory = RideContinuityMemory()
    snare_memory: SnarePhraseMemory = SnarePhraseMemory()
    legend: DrumLegendProjection | None = None

    def validate(self) -> None:
        self.soloist.validate()
        self.phrase_memory.validate()
        if self.bass is not None:
            self.bass.validate()
        self.ride_memory.validate()
        self.snare_memory.validate()

    @classmethod
    def from_ensemble_state(
        cls,
        *,
        soloist: SoloistEnergyProjection,
        phrase_memory: BebopPhraseMemory,
        ensemble_state: EnsembleState,
    ) -> "BebopRuntimeProjection":
        """Build a drum-owned projection without copying Shared Core semantics."""
        return cls(
            soloist=soloist,
            phrase_memory=phrase_memory,
            bass=project_bass_pulse(ensemble_state),
            ride_memory=RideContinuityMemory(),
            snare_memory=SnarePhraseMemory(),
            legend=None,
        )


@dataclass(frozen=True)
class BebopScoredGesture:
    gesture: DrumGesture
    score: float
    interaction: BebopInteractionDecision
    comp_intent: BebopCompIntent
    bass_intent: BassDrumIntent | None
    components: tuple[tuple[str, float], ...] = ()


def _contains_voice(gesture: DrumGesture, voice: DrumVoice) -> bool:
    return any(hit.voice is voice for hit in gesture.hits)


def _bass_intent(
    gesture: DrumGesture,
    interaction: BebopInteractionDecision,
    context: DrummerRuntimeContext,
) -> BassDrumIntent | None:
    if not _contains_voice(gesture, DrumVoice.BASS_DRUM):
        return None
    if context.requested_kick or "explicit_cue" in gesture.tags:
        return BassDrumIntent.ENSEMBLE_FIGURE_SUPPORT
    if gesture.role is GestureRole.SETUP:
        return BassDrumIntent.SETUP
    if interaction.state in {BebopInteractionState.BUILD, BebopInteractionState.HANDOFF}:
        return BassDrumIntent.INTERACTIVE_ACCENT
    return BassDrumIntent.FLOOR_SUPPORT


def _intentional_non_response_candidate() -> DrumGesture:
    return DrumGesture(
        role=GestureRole.SPACE,
        tags=frozenset({
            "bebop",
            "intentional_non_response",
            "listening_action",
        }),
        provenance=("drum_player", "bebop_runtime"),
    )


def _quiet_bass_floor_candidate(
    base: tuple[DrumHit, ...],
    plan: DrummerSoftPlan,
) -> DrumGesture | None:
    if any(hit.limb is Limb.RIGHT_FOOT for hit in base):
        return None
    hit = DrumHit(
        DrumVoice.BASS_DRUM,
        Limb.RIGHT_FOOT,
        velocity=max(24, min(48, int(30 + 18 * plan.energy))),
        microtiming_ms=plan.microtiming_bias_ms,
        articulation="floor_support",
    )
    gesture = DrumGesture(
        hits=base + (hit,),
        role=GestureRole.COMP,
        tags=frozenset({"bebop", "bass_floor_support", "timekeeping"}),
        provenance=("drum_player", "bebop_runtime"),
    )
    gesture.validate()
    return gesture


def build_bebop_candidates(
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
    projection: BebopRuntimeProjection,
) -> tuple[DrumGesture, ...]:
    """Build immediate generic + bebop-specific candidates."""
    plan.validate()
    context.validate()
    projection.validate()

    interaction = infer_bebop_interaction_state(
        projection.soloist,
        projection.phrase_memory,
        drummer_energy=plan.energy,
        phrase_position=context.phrase_position,
        section_transition=context.section_transition,
    )

    generic = list(build_immediate_candidates(plan, context))

    # Generic snare comping is replaced by phrase-memory-aware bebop comping.
    generic = [
        g for g in generic
        if "snare_comp" not in g.tags
    ]

    # Replace the generic canonical ride-time gesture with a bebop continuity
    # surface. Keep any simultaneous non-ride anchor (e.g. pedal hi-hat 2&4).
    canonical_time = next(
        (
            g for g in generic
            if g.role is GestureRole.TIME
            and "timekeeping" in g.tags
            and "source_pattern" not in g.tags
        ),
        None,
    )
    auxiliary_hits: tuple[DrumHit, ...] = ()
    if canonical_time is not None:
        auxiliary_hits = tuple(
            h for h in canonical_time.hits if h.voice is not DrumVoice.RIDE
        )
        generic.remove(canonical_time)

    for ride_candidate in build_ride_candidates(
        plan,
        context,
        interaction.state,
        projection.ride_memory,
        bass=projection.bass,
    ):
        combined = DrumGesture(
            hits=ride_candidate.gesture.hits + auxiliary_hits,
            role=ride_candidate.gesture.role,
            tags=ride_candidate.gesture.tags,
            confidence=ride_candidate.gesture.confidence,
            provenance=ride_candidate.gesture.provenance,
        )
        combined.validate()
        generic.append(combined)

    for snare_candidate in build_snare_phrase_candidates(
        plan,
        context,
        interaction.state,
        choose_comp_intent(
            interaction,
            projection.phrase_memory,
            phrase_position=context.phrase_position,
        ),
        projection.snare_memory,
    ):
        generic.append(snare_candidate.gesture)

    generic.append(_intentional_non_response_candidate())

    # Offer a very quiet bass-floor version only on top of a currently clear
    # time-bearing gesture; never manufacture future pulse events.
    time_gesture = next(
        (g for g in generic if g.role is GestureRole.TIME and g.hits),
        None,
    )
    if time_gesture is not None:
        floor = _quiet_bass_floor_candidate(time_gesture.hits, plan)
        if floor is not None:
            generic.append(floor)

    # Deduplicate by musical surface + tags.
    seen: set[tuple[tuple[tuple[str, str, int, str], ...], tuple[str, ...], str]] = set()
    out: list[DrumGesture] = []
    for gesture in generic:
        key = (
            tuple((h.voice.value, h.limb.value, h.velocity, h.articulation) for h in gesture.hits),
            tuple(sorted(gesture.tags)),
            gesture.role.value,
        )
        if key not in seen:
            seen.add(key)
            out.append(gesture)
    return tuple(out)


def score_bebop_gesture(
    gesture: DrumGesture,
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
    projection: BebopRuntimeProjection,
    profile: BebopStyleProfile = DEFAULT_BEBOP_PROFILE,
) -> BebopScoredGesture:
    """Score one immediate gesture using generic and bebop-specific semantics."""
    profile.validate()
    projection.validate()

    interaction = infer_bebop_interaction_state(
        projection.soloist,
        projection.phrase_memory,
        drummer_energy=plan.energy,
        phrase_position=context.phrase_position,
        section_transition=context.section_transition,
    )
    comp_intent = choose_comp_intent(
        interaction,
        projection.phrase_memory,
        phrase_position=context.phrase_position,
    )
    bass_intent = _bass_intent(gesture, interaction, context)

    base: ScoredDrumGesture = score_gesture(gesture, plan, context)
    score = base.score
    components = list(base.components)

    if _contains_voice(gesture, DrumVoice.RIDE):
        v = 0.28 * profile.ride_time_salience.value
        score += v
        components.append(("bebop_ride_salience", v))

    if "ride_continuity" in gesture.tags:
        v = score_ride_surface_gesture(
            gesture,
            plan,
            context,
            interaction.state,
            projection.ride_memory,
            bass=projection.bass,
            profile=profile,
        )
        score += v
        components.append(("ride_surface_continuity", v))

    if "intentional_non_response" in gesture.tags:
        if comp_intent is BebopCompIntent.INTENTIONAL_NON_RESPONSE:
            v = 0.62 * profile.intentional_non_response.value
        elif interaction.state is BebopInteractionState.LISTEN:
            v = 0.24 * profile.intentional_non_response.value
        else:
            v = -0.20
        score += v
        components.append(("intentional_non_response", v))

    if "snare_phrase" in gesture.tags:
        phrase_candidates = build_snare_phrase_candidates(
            plan,
            context,
            interaction.state,
            comp_intent,
            projection.snare_memory,
        )
        matching = next(
            (
                candidate for candidate in phrase_candidates
                if candidate.action.value in gesture.tags
            ),
            None,
        )
        if matching is not None:
            v = matching.score_bias
            score += v
            components.append(("snare_phrase_development", v))
            if matching.relation_to_motif > 0:
                mv = 0.16 * matching.relation_to_motif
                score += mv
                components.append(("snare_motif_relation", mv))

    if gesture.role is GestureRole.COMP:
        # Selectivity penalizes generic activity when the interaction state asks
        # the drummer to coast/listen.
        if interaction.state in {BebopInteractionState.COAST, BebopInteractionState.LISTEN}:
            v = -0.34 * profile.comp_selectivity.value
            score += v
            components.append(("bebop_comp_selectivity", v))
        elif interaction.state is BebopInteractionState.BUILD:
            v = 0.24 * profile.comp_selectivity.value
            score += v
            components.append(("bebop_build_comp", v))
        elif interaction.state is BebopInteractionState.COME_DOWN:
            v = -0.16 * profile.comp_selectivity.value
            score += v
            components.append(("bebop_come_down", v))

    if bass_intent is BassDrumIntent.FLOOR_SUPPORT:
        if "bass_floor_support" in gesture.tags:
            v = 0.26 * profile.bass_floor_support.value
            if interaction.state is BebopInteractionState.COAST:
                v += 0.08
            score += v
            components.append(("bass_floor_support", v))
        elif "bass_drum_comp" in gesture.tags:
            # Generic kick-comp articulation is less desirable when the musical
            # role is actually floor support.
            v = -0.16
            score += v
            components.append(("avoid_ambiguous_bass_role", v))

    if bass_intent is BassDrumIntent.INTERACTIVE_ACCENT:
        if "bass_drum_comp" in gesture.tags or "explicit_cue" in gesture.tags:
            v = 0.22 * profile.bass_interactive_accent.value
            score += v
            components.append(("bass_interactive_accent", v))

    if gesture.role is GestureRole.SETUP and (
        context.phrase_position >= 0.82 or context.section_transition
    ):
        v = 0.18 * profile.form_punctuation_opportunity.value
        score += v
        components.append(("form_punctuation_opportunity", v))

    # Phrase pacing: discourage another statement after a recently dense spell.
    if gesture.role in {GestureRole.COMP, GestureRole.SETUP, GestureRole.ACCENT}:
        recent = projection.phrase_memory.recent_comp_density
        if recent > 0.62:
            v = -0.24 * profile.phrase_pacing_memory.value * recent
            score += v
            components.append(("phrase_pacing_memory", v))

    # Shared Legend Intelligence affects ranking through drummer-specific
    # realization features; it never inserts a precomposed future phrase.
    if projection.legend is not None:
        delta, parts = legend_gesture_adjustment(gesture, projection.legend)
        score += delta
        components.extend(parts)

    # Bass/drums coupling is complementary rather than a synchronous-hit reward.
    if projection.bass is not None:
        coupling = infer_bass_drums_coupling(
            projection.bass,
            interaction_state=interaction.state,
        )
        delta, parts = coupling_score_adjustment(
            gesture,
            bass_intent=bass_intent,
            coupling=coupling,
        )
        score += delta
        components.extend(parts)

    return BebopScoredGesture(
        gesture=gesture,
        score=score,
        interaction=interaction,
        comp_intent=comp_intent,
        bass_intent=bass_intent,
        components=tuple(components),
    )


def perform_one_bebop_gesture(
    plan: DrummerSoftPlan,
    context: DrummerRuntimeContext,
    projection: BebopRuntimeProjection,
    memory: DrummerPerformanceMemory,
    profile: BebopStyleProfile = DEFAULT_BEBOP_PROFILE,
) -> BebopScoredGesture:
    """Commit one bebop-aware immediate gesture, then listen/re-plan."""
    candidates = build_bebop_candidates(plan, context, projection)
    chosen = max(
        (score_bebop_gesture(g, plan, context, projection, profile) for g in candidates),
        key=lambda x: x.score,
    )
    memory.commit(chosen.gesture)
    return chosen
