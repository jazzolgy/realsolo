"""Piano solo policy using bebop melodic priors.

Charlie Parker is the first default melodic LegendProfile, not the identity of the
piano player. The profile biases immediate note decisions; piano realization,
register, touch, and accompaniment interaction remain instrument-local.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from music_intelligence.legends.parker import PARKER_PROFILE_VIEW
from music_intelligence.reasoning.legend_style_core import (
    CandidateEvent,
    CandidateScore,
    LegendBlend,
    MusicalContextVector,
)
from music_intelligence.reasoning.online_improviser import (
    OnlineMusicalEvaluator,
    PerformanceMemory,
    SoftPlan,
)
from music_intelligence.learning.engine import LearningPriorView
from music_intelligence.reasoning.learning_prior_runtime import circular_phase_bias

from .bebop_phrase_space import BebopPhraseSpaceEvidence, PhraseSpaceType
from .bebop_complementarity import (
    EnsembleBreathType,
    EnsembleComplementarityEvidence,
    SupportCarryMode,
    support_carry_mode,
)
from .bebop_turn_taking import BebopTurnTakingEvidence, BebopTurnTakingType
from .bebop_harmonic_turn import (
    BebopHarmonicPhase,
    BebopHarmonicTurnContext,
)


def default_bebop_legend_blend() -> LegendBlend:
    """Consume Charlie Parker through the shared LegendProfileView interface."""
    return PARKER_PROFILE_VIEW.blend()


@dataclass(frozen=True)
class PianoSoloContext:
    musical: MusicalContextVector = field(default_factory=MusicalContextVector)
    right_hand_low_midi: int = 48
    right_hand_high_midi: int = 96
    left_hand_comping_activity: float = 0.35
    left_hand_harmonic_coverage: float = 0.35
    left_hand_rhythmic_coverage: float = 0.35
    left_hand_register_top_midi: int | None = None
    ensemble_density: float = 0.5
    creativity_strength: float = 0.6
    previous_pitch_midi: int | None = None
    comfortable_leap_semitones: int = 5
    phrase_space: BebopPhraseSpaceEvidence = field(
        default_factory=BebopPhraseSpaceEvidence
    )
    ensemble_complementarity: EnsembleComplementarityEvidence = field(
        default_factory=EnsembleComplementarityEvidence
    )
    turn_taking: BebopTurnTakingEvidence = field(
        default_factory=lambda: BebopTurnTakingEvidence(
            BebopTurnTakingType.AMBIGUOUS,
            1.0,
            1.0,
            1.0,
            1.0,
            0.0,
            0.0,
        )
    )
    harmonic_turn: BebopHarmonicTurnContext = field(
        default_factory=BebopHarmonicTurnContext
    )

    def validate(self) -> None:
        if not 21 <= self.right_hand_low_midi <= 108:
            raise ValueError("right_hand_low_midi outside piano range")
        if not 21 <= self.right_hand_high_midi <= 108:
            raise ValueError("right_hand_high_midi outside piano range")
        if self.right_hand_low_midi >= self.right_hand_high_midi:
            raise ValueError("right-hand range must be ascending")
        for name in (
            "left_hand_comping_activity",
            "left_hand_harmonic_coverage",
            "left_hand_rhythmic_coverage",
            "ensemble_density",
            "creativity_strength",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.previous_pitch_midi is not None and not 21 <= self.previous_pitch_midi <= 108:
            raise ValueError("previous_pitch_midi outside piano range")
        if not 1 <= self.comfortable_leap_semitones <= 12:
            raise ValueError("comfortable_leap_semitones must be within 1..12")
        if (
            self.left_hand_register_top_midi is not None
            and not 21 <= self.left_hand_register_top_midi <= 108
        ):
            raise ValueError("left_hand_register_top_midi must be within MIDI range")
        self.phrase_space.validate()
        self.ensemble_complementarity.validate()
        self.turn_taking.validate()
        self.harmonic_turn.validate()


@dataclass
class PianoSoloState:
    memory: PerformanceMemory = field(default_factory=PerformanceMemory)

    @property
    def previous_pitch_midi(self) -> int | None:
        for event in reversed(self.memory.committed):
            if event.pitch_midi is not None:
                return event.pitch_midi
        return None


class PianoSoloEvaluator:
    """Immediate monophonic piano-solo evaluator.

    Shared bebop/legend logic remains generic. This layer only adds piano-local
    constraints and accompaniment-space considerations.
    """

    def __init__(
        self,
        legend_blend: LegendBlend | None = None,
        solo_phrase_prior: LearningPriorView | None = None,
    ):
        self.legend_blend = legend_blend or default_bebop_legend_blend()
        self.shared = OnlineMusicalEvaluator(self.legend_blend)
        self.solo_phrase_prior = solo_phrase_prior

    def evaluate(
        self,
        candidate: CandidateEvent,
        context: PianoSoloContext,
    ) -> CandidateScore:
        context.validate()
        base = self.shared.evaluate(candidate, context.musical)

        score = base.total
        components = dict(base.components)
        reasons = list(base.reasons)

        if candidate.pitch_midi is not None:
            if not 21 <= candidate.pitch_midi <= 108:
                components["piano_range"] = -10.0
                reasons.append("candidate lies outside physical piano range")
                return CandidateScore(candidate, score - 10.0, components, tuple(reasons))

            if not (
                context.right_hand_low_midi
                <= candidate.pitch_midi
                <= context.right_hand_high_midi
            ):
                components["right_hand_register"] = -0.18
                score -= 0.18
                reasons.append("candidate leaves preferred right-hand solo register")

        tags = set(candidate.tags)

        learned_entry = circular_phase_bias(
            self.solo_phrase_prior,
            "entry_phase",
            context.musical.metric_position + candidate.onset_offset_beats,
            cycle=4.0,
            tolerance=1.0,
        )
        if learned_entry.active:
            components["learned_solo_entry_phase"] = learned_entry.score_delta
            score += learned_entry.score_delta
            reasons.append(learned_entry.reason)

        # Parker-informed lines should sound directed and singable, not merely
        # harmonically complicated. Prefer small/medium motion; allow larger leaps
        # when they clearly land on structural/resolution targets.
        if candidate.pitch_midi is not None and context.previous_pitch_midi is not None:
            interval = abs(candidate.pitch_midi - context.previous_pitch_midi)
            directed = bool(
                {"guide_tone","directed_target","resolution_path","next_harmony_target"}
                & tags
            )
            connector = bool(
                {"close_approach","neighbor","passing","enclosure","connector"} & tags
            )
            if interval <= 2 and connector:
                components["accessible_bebop_motion"] = 0.085
                score += 0.085
                reasons.append("small directed connector makes bebop line audible and playable")
            elif interval <= context.comfortable_leap_semitones:
                components["comfortable_motion"] = 0.045
                score += 0.045
                reasons.append("moderate interval supports singable bebop continuity")
            elif interval >= 8 and not directed:
                components["undirected_large_leap"] = -0.13
                score -= 0.13
                reasons.append("large leap lacks structural target and sounds unnecessarily difficult")
            elif interval >= 8 and directed:
                components["directed_large_leap"] = 0.015
                score += 0.015
                reasons.append("larger leap is tolerated because it lands on a structural target")

        # Keep Parker chromatic language target-directed rather than chaining
        # successive color notes without harmonic identity.
        if context.musical.recent_altered_density >= .55:
            if "altered" in tags and not (
                {"guide_tone","directed_target","resolution_path","next_harmony_target"} & tags
            ):
                components["altered_density_restraint"] = -0.09
                score -= 0.09
                reasons.append("recent altered density calls for a clearer target")

        # Busy LH/ensemble texture should redirect the solo toward clarity, not
        # suppress melodic creativity entirely.
        if (
            context.left_hand_comping_activity >= 0.7
            or context.ensemble_density >= 0.75
        ):
            if "rest" in tags or candidate.pitch_midi is None:
                components["texture_space"] = 0.12
                score += 0.12
                reasons.append("space protects clarity over busy accompaniment")
            if "dense_run" in tags:
                components["texture_crowding"] = -0.12
                score -= 0.12
                reasons.append("dense run competes with active accompaniment")

        # Bebop is the initial priority: directed chromaticism is favored more than
        # undirected chromatic saturation.
        if {"close_approach", "neighbor", "passing"} & tags:
            components["piano_bebop_connector"] = 0.05
            score += 0.05
            reasons.append("bebop connector remains idiomatic on piano")

        if "altered" in tags and not (
            {"directed_target", "resolution_path"} & tags
        ):
            components["undirected_chromaticism"] = -0.08
            score -= 0.08
            reasons.append("chromatic color lacks an audible target or return path")

        space = context.phrase_space
        if space.space_type is PhraseSpaceType.QUIET_ACTIVE:
            weight = space.confidence * max(space.energy_drop, 0.25)
            if candidate.pitch_midi is None or "rest" in tags:
                v = 0.08 * weight
                score += v
                components["quiet_active_space"] = v
                reasons.append("quiet-active phrase space can remain open")
            if "dense_run" in tags:
                v = -0.06 * weight
                score += v
                components["quiet_active_density"] = v
                reasons.append("dense run may erase quiet-active ensemble space")
            if (
                space.percussive_support >= 0.65
                and {"anticipation", "pickup", "syncopated_entry"} & tags
            ):
                v = 0.05 * weight * space.percussive_support
                score += v
                components["rhythm_section_carried_space"] = v
                reasons.append(
                    "percussive support remains active, favoring a rhythmic re-entry"
                )

        elif space.space_type is PhraseSpaceType.DEEP_RELEASE:
            weight = space.confidence * max(space.energy_drop, 0.5)
            if {"phrase_entry", "pickup", "anticipation"} & tags:
                v = 0.10 * weight
                score += v
                components["deep_release_reentry"] = v
                reasons.append("deep release creates a clear re-entry opportunity")
            if (
                space.reentry_contrast >= 0.35
                and {"directed_target", "resolution_path"} & tags
            ):
                v = 0.07 * weight
                score += v
                components["reentry_direction"] = v
                reasons.append("strong post-space contrast favors a directed re-entry")
            if candidate.pitch_midi is None and space.reentry_contrast < 0.25:
                v = 0.04 * weight
                score += v
                components["deep_release_hold_space"] = v
                reasons.append("deep release need not be filled immediately")

        if candidate.pitch_midi is not None:
            if (
                context.left_hand_register_top_midi is not None
                and context.left_hand_comping_activity >= 0.55
                and candidate.pitch_midi - context.left_hand_register_top_midi <= 5
            ):
                components["left_hand_register_collision"] = -0.10
                score -= 0.10
                reasons.append("right-hand solo crowds active left-hand register")

            if context.left_hand_harmonic_coverage <= 0.25:
                if {"chord_tone", "guide_tone", "harmonic_identity"} & tags:
                    v = 0.06
                    components["right_hand_harmonic_support"] = v
                    score += v
                    reasons.append(
                        "right hand can clarify harmony when left-hand coverage is sparse"
                    )
            elif context.left_hand_harmonic_coverage >= 0.75:
                if "harmonic_outline" in tags and "connector" not in tags:
                    v = -0.05
                    components["duplicate_harmonic_outline"] = v
                    score += v
                    reasons.append(
                        "explicit right-hand outlining duplicates dense left-hand harmony"
                    )

            if context.left_hand_rhythmic_coverage >= 0.75 and "dense_run" in tags:
                v = -0.06
                components["left_hand_rhythmic_crowding"] = v
                score += v
                reasons.append(
                    "dense right-hand run competes with active left-hand rhythmic coverage"
                )

        complementarity = context.ensemble_complementarity
        if complementarity.breath_type is EnsembleBreathType.FOREGROUND_HANDOFF:
            weight = complementarity.confidence * complementarity.foreground_drop
            carry_mode = support_carry_mode(complementarity)
            if candidate.pitch_midi is None or "rest" in tags:
                v = 0.07 * weight
                score += v
                components["foreground_handoff_space"] = v
                reasons.append("foreground handoff can remain open over active support")
            if {"pickup", "anticipation", "syncopated_entry"} & tags:
                support = max(
                    complementarity.low_harmonic_support,
                    complementarity.percussive_support,
                )
                v = 0.06 * weight * support
                score += v
                components["foreground_handoff_pickup"] = v
                reasons.append("active support favors a light rhythmic pickup")
            if "dense_run" in tags:
                v = -0.08 * weight
                score += v
                components["foreground_handoff_overfill"] = v
                reasons.append("dense run can overfill an already-supported handoff")
            if carry_mode is SupportCarryMode.HARMONIC_CARRIED:
                if "harmonic_outline" in tags:
                    v = -0.05 * weight
                    score += v
                    components["harmonic_carried_avoid_outline"] = v
                    reasons.append("harmonic support already carries the handoff; avoid duplicate outlining")
                if {"pickup", "anticipation", "connector"} & tags:
                    v = 0.04 * weight
                    score += v
                    components["harmonic_carried_melodic_response"] = v
                    reasons.append("harmonic-carried space leaves room for a light melodic/rhythmic response")

            elif carry_mode is SupportCarryMode.PERCUSSIVE_CARRIED:
                if {"guide_tone", "harmonic_identity"} & tags:
                    v = 0.04 * weight
                    score += v
                    components["percussive_carried_harmonic_support"] = v
                    reasons.append("percussive-carried handoff can admit a thin harmonic anchor")

            elif carry_mode is SupportCarryMode.MIXED_SUPPORT:
                if candidate.pitch_midi is None or "rest" in tags:
                    v = 0.05 * weight
                    score += v
                    components["mixed_support_preserve_space"] = v
                    reasons.append("harmonic and percussive support already carry the handoff")


        elif complementarity.breath_type is EnsembleBreathType.COLLECTIVE_RELEASE:
            weight = complementarity.confidence * complementarity.foreground_drop
            if (
                complementarity.post_foreground_reentry >= 0.35
                and {"phrase_entry", "directed_target", "resolution_path"} & tags
            ):
                v = 0.09 * weight
                score += v
                components["collective_release_reentry"] = v
                reasons.append("collective release can frame a new directed phrase entry")
            elif candidate.pitch_midi is None:
                v = 0.04 * weight
                score += v
                components["collective_release_hold"] = v
                reasons.append("collective release may be allowed to breathe")

        turn = context.turn_taking
        if (
            turn.episode_type is BebopTurnTakingType.SUPPORTED_HANDOFF_REENTRY
            and turn.confidence > 0
        ):
            weight = turn.confidence * min(1.0, turn.reentry_strength / 4.0)
            if {"continuation", "connector", "directed_target"} & tags:
                v = 0.05 * weight
                score += v
                components["turn_reentry_continuation"] = v
                reasons.append("recent supported handoff already re-entered; continue rather than restart")
            if "phrase_entry" in tags:
                v = -0.03 * weight
                score += v
                components["turn_duplicate_entry"] = v
                reasons.append("avoid treating an already-reentered phrase as another fresh entry")

        elif (
            turn.episode_type is BebopTurnTakingType.COLLECTIVE_RELEASE_REENTRY
            and turn.confidence > 0
        ):
            weight = turn.confidence * min(1.0, turn.reentry_strength / 4.0)
            if {"continuation", "resolution_path"} & tags:
                v = 0.04 * weight
                score += v
                components["collective_reentry_continuation"] = v
                reasons.append("collective release has already resolved into re-entry; support phrase continuation")

        elif (
            turn.episode_type is BebopTurnTakingType.FOREGROUND_CONTINUES
            and turn.confidence > 0
        ):
            weight = turn.confidence
            if candidate.pitch_midi is None or "rest" in tags:
                v = 0.05 * weight
                score += v
                components["foreground_continues_contrast"] = v
                reasons.append("continued foreground activity can justify immediate contrast or space")
            if "dense_run" in tags:
                v = -0.04 * weight
                score += v
                components["foreground_continues_overdensity"] = v
                reasons.append("continued foreground activity argues against another dense layer")

        harmonic_turn = context.harmonic_turn
        if harmonic_turn.confidence > 0:
            weight = harmonic_turn.confidence

            if harmonic_turn.phase is BebopHarmonicPhase.ANTICIPATORY:
                if {"anticipation", "pickup", "next_harmony_target"} & tags:
                    v = 0.08 * weight * max(
                        harmonic_turn.anticipation_strength,
                        0.5,
                    )
                    score += v
                    components["harmonic_turn_anticipation"] = v
                    reasons.append(
                        "turn-taking re-entry aligns with known future harmony"
                    )
                if "routine_downbeat_entry" in tags:
                    v = -0.04 * weight
                    score += v
                    components["harmonic_turn_downbeat_rigidity"] = v
                    reasons.append(
                        "known next harmony leaves room for anticipatory re-entry"
                    )

            elif harmonic_turn.phase is BebopHarmonicPhase.DIRECTED_RESOLUTION:
                if {"directed_target", "resolution_path", "guide_tone"} & tags:
                    v = 0.08 * weight * max(
                        harmonic_turn.resolution_strength,
                        0.5,
                    )
                    score += v
                    components["harmonic_turn_resolution"] = v
                    reasons.append(
                        "directed harmonic moment favors audible target/resolution"
                    )
                if "undirected_outside" in tags:
                    v = -0.05 * weight
                    score += v
                    components["harmonic_turn_undirected_outside"] = v
                    reasons.append(
                        "resolution pressure argues against directionless outside color"
                    )

            elif harmonic_turn.phase is BebopHarmonicPhase.STABLE_FIELD:
                if {"connector", "color_tone", "motif_continuation"} & tags:
                    v = 0.04 * weight * max(
                        harmonic_turn.stability_strength,
                        0.5,
                    )
                    score += v
                    components["harmonic_turn_stable_field"] = v
                    reasons.append(
                        "stable field permits connective/color development"
                    )

            elif harmonic_turn.phase is BebopHarmonicPhase.FORM_BOUNDARY:
                if {"phrase_entry", "phrase_end", "register_reset", "texture_reset"} & tags:
                    v = 0.07 * weight * max(
                        harmonic_turn.phrase_boundary_pressure,
                        0.5,
                    )
                    score += v
                    components["harmonic_turn_form_boundary"] = v
                    reasons.append(
                        "form boundary permits phrase/texture reset"
                    )
                if "automatic_continuation" in tags:
                    v = -0.04 * weight
                    score += v
                    components["harmonic_turn_boundary_overrun"] = v
                    reasons.append(
                        "form boundary should not be ignored by automatic continuation"
                    )

        return CandidateScore(candidate, score, components, tuple(reasons))

    def choose_immediate(
        self,
        candidates: Sequence[CandidateEvent],
        context: PianoSoloContext,
    ) -> CandidateScore:
        if not candidates:
            raise ValueError("no piano solo candidates")
        return max(
            (self.evaluate(candidate, context) for candidate in candidates),
            key=lambda item: item.total,
        )


def perform_one_piano_solo_event(
    plan: SoftPlan,
    evaluator: PianoSoloEvaluator,
    candidates: Sequence[CandidateEvent],
    context: PianoSoloContext,
    state: PianoSoloState,
) -> CandidateScore:
    """Choose and commit one immediate solo event, then the system must re-listen."""
    plan.validate_for_improvisation()
    chosen = evaluator.choose_immediate(candidates, context)
    state.memory.commit(chosen.candidate)
    return chosen
