"""Experimental context-aware jazz piano comping decision layer.

This module is intentionally small. It tests whether the pianist can choose among
silence and a few immediate sounding gestures from ensemble/phrase context while
consuming Shared Core harmonic affordances without rebuilding harmony theory locally.

Research basis: McNeely comping study v0.1. The role/action labels are RealSolo design
inferences and remain provisional until cross-source validation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence

from music_intelligence.harmony.jazz_harmony_core import HarmonicAffordance, HarmonicFrame
from music_intelligence.harmony.orchestrator import HarmonicReasoningResult
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from music_intelligence.reasoning.online_improviser import SoftPlan
from music_intelligence.reasoning.harmonic_player_bridge import harmonic_guidance_for_candidate

from .policy import (
    PianoActionScore,
    PianoPerformanceState,
    PianoPolicyEvaluator,
    PianoRealizationCandidate,
)
from .interaction import (
    EnergyDirection,
    PhraseSpaceWindow,
    PianoDensity,
    PianoInteractionState,
    blend_density,
    decay_density,
    infer_energy_direction,
)
from .narrative import evaluate_narrative_bias
from .variation import GestureSignature, VariationContext, evaluate_variation
from .ensemble_response import (
    EnsembleResponseObservation,
    EnsembleSnapshot,
    GestureResponseRecord,
    evaluate_response_bias,
    infer_coarse_responses,
)
from .interaction_episode import (
    InteractionEpisode,
    evaluate_episode_bias,
    infer_interaction_episode,
)
from .role_occupancy import (
    CompingRoleOccupancy,
    evaluate_role_occupancy_bias,
)
from .harmonic_continuity import (
    HarmonicContinuityFeatures,
    HarmonicContinuityMemory,
)
from .creative_continuity import (
    CreativityContext,
    evaluate_creative_continuity,
    profile_from_harmonic_context,
)
from .harmonic_creativity import (
    adapt_continuity_profile_for_harmony,
    adapt_creativity_context_for_harmony,
)
from .bebop_harmonic_turn import BebopHarmonicTurnContext
from .bebop_harmonic_turn_comping import (
    evaluate_bebop_harmonic_turn_comping_bias,
)
from .ensemble_role import PianoEnsembleMode
from .lh_texture import evaluate_lh_texture_bias
from .lh_voice_leading import evaluate_lh_voice_leading
from .rh_lh_interaction import evaluate_rh_lh_interaction


class InteractionRole(str, Enum):
    LAY_OUT = "lay_out"
    SUPPORT = "support"
    ANCHOR = "anchor"
    PUNCTUATE = "punctuate"
    ANSWER = "answer"
    FILL = "fill"
    BUILD = "build"
    RELEASE = "release"


class CompingActionType(str, Enum):
    SILENCE = "silence"
    SPARSE_SUPPORT = "sparse_support"
    PUNCTUATION = "punctuation"
    RESPONSE = "response"
    SUSTAINED_SUPPORT = "sustained_support"


@dataclass(frozen=True)
class PianoCompingContext:
    """Piano-local experimental projection of currently perceived ensemble state."""

    soloist_activity: float = 0.5
    piano_foreground_activity: float = 0.0
    piano_foreground_register_midi: float | None = None
    piano_foreground_onset_proximity_beats: float | None = None
    piano_foreground_gap_beats: float = 0.0
    piano_foreground_rhythm_match_confidence: float = 0.0
    phrase_boundary_probability: float = 0.0
    available_space_beats: float = 0.0
    bass_activity: float = 0.5
    drummer_activity: float = 0.5
    ensemble_density: float = 0.5
    recent_piano_density: float = 0.0
    section_energy: float = 0.5
    soloist_register_midi: float | None = None
    variation_pressure: float = 0.5
    groove_lock_strength: float = 0.0
    motif_continuity_strength: float = 0.0
    pattern_consistency_strength: float = 0.0
    auto_pattern_consistency: bool = True
    creativity_strength: float = 0.55
    creativity_coherence_floor: float = 0.30
    tension_preference: float = 0.62
    role_occupancy: CompingRoleOccupancy = field(default_factory=CompingRoleOccupancy)
    harmonic_turn: BebopHarmonicTurnContext = field(
        default_factory=BebopHarmonicTurnContext
    )
    ensemble_mode: PianoEnsembleMode = PianoEnsembleMode.EXTERNAL_MELODY_SUPPORT
    time_feel: str = "swing"

    def validate(self) -> None:
        for name in (
            "soloist_activity",
            "piano_foreground_activity",
            "piano_foreground_rhythm_match_confidence",
            "phrase_boundary_probability",
            "bass_activity",
            "drummer_activity",
            "ensemble_density",
            "recent_piano_density",
            "section_energy",
            "variation_pressure",
            "groove_lock_strength",
            "motif_continuity_strength",
            "pattern_consistency_strength",
            "creativity_strength",
            "creativity_coherence_floor",
            "tension_preference",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.available_space_beats < 0:
            raise ValueError("available_space_beats cannot be negative")
        if self.piano_foreground_gap_beats < 0:
            raise ValueError("piano_foreground_gap_beats cannot be negative")
        if (
            self.piano_foreground_onset_proximity_beats is not None
            and self.piano_foreground_onset_proximity_beats < 0
        ):
            raise ValueError("piano_foreground_onset_proximity_beats cannot be negative")
        if self.soloist_register_midi is not None and not 0 <= self.soloist_register_midi <= 127:
            raise ValueError("soloist_register_midi must be within MIDI range")
        if (
            self.piano_foreground_register_midi is not None
            and not 0 <= self.piano_foreground_register_midi <= 127
        ):
            raise ValueError("piano_foreground_register_midi must be within MIDI range")
        self.role_occupancy.validate()
        self.harmonic_turn.validate()


@dataclass(frozen=True)
class PianoCompingCandidate:
    """One immediate comping decision.

    Silence is represented directly rather than encoded as a fake empty voicing.
    Sounding candidates wrap the shared-Core polyphonic event through
    PianoRealizationCandidate.
    """

    action_type: CompingActionType
    role: InteractionRole
    duration_beats: float
    realization: PianoRealizationCandidate | None = None
    harmonic_affordance_id: str | None = None
    tags: frozenset[str] = frozenset()

    def validate(self) -> None:
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")
        if self.action_type is CompingActionType.SILENCE:
            if self.realization is not None:
                raise ValueError("silence must not carry a sounding realization")
            return
        if self.realization is None:
            raise ValueError("sounding comping action requires a piano realization")
        self.realization.validate()


@dataclass(frozen=True)
class PianoCompingScore:
    candidate: PianoCompingCandidate
    total: float
    components: Mapping[str, float] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()
    piano_score: PianoActionScore | None = None


@dataclass
class PianoCompingState:
    piano: PianoPerformanceState = field(default_factory=PianoPerformanceState)
    committed: list[PianoCompingCandidate] = field(default_factory=list)
    recent_density: PianoDensity = field(default_factory=PianoDensity)
    last_family: str | None = None
    last_role: str | None = None
    sounding_streak: int = 0
    silence_streak: int = 0
    last_section_energy: float | None = None
    recent_signatures: list[GestureSignature] = field(default_factory=list)
    recent_responses: list[GestureResponseRecord] = field(default_factory=list)
    active_episode: InteractionEpisode | None = None
    harmonic_continuity: HarmonicContinuityMemory = field(default_factory=HarmonicContinuityMemory)
    last_harmonic_continuity: HarmonicContinuityFeatures | None = None

    @staticmethod
    def _estimate_density(candidate: PianoCompingCandidate) -> PianoDensity:
        if candidate.realization is None:
            return PianoDensity()

        event = candidate.realization.event
        pitches = event.pitches_midi
        voice_count = len(pitches)
        span = float(max(pitches) - min(pitches)) if pitches else 0.0
        duration = max(candidate.duration_beats, 0.125)
        onset_rate = min(4.0, 1.0 / duration)
        sustain_ratio = min(1.0, duration / 2.0)
        concentration = 0.0
        if voice_count > 1 and span > 0:
            concentration = min(1.0, (voice_count - 1) / max(span / 12.0, 1.0) / 4.0)
        dynamic_weight = min(1.0, event.velocity / 127.0)
        pedal_blur = 0.0
        if candidate.realization.pedal == "sustain":
            pedal_blur = 1.0
        elif candidate.realization.pedal == "half":
            pedal_blur = 0.6
        elif candidate.realization.pedal in {"flutter", "sostenuto"}:
            pedal_blur = 0.35

        return PianoDensity(
            voice_count=voice_count,
            onset_rate=onset_rate,
            sustain_ratio=sustain_ratio,
            register_span=span,
            registral_concentration=concentration,
            dynamic_weight=dynamic_weight,
            pedal_blur=pedal_blur,
        )

    def commit(
        self,
        candidate: PianoCompingCandidate,
        *,
        section_energy: float | None = None,
    ) -> None:
        candidate.validate()
        if section_energy is not None and not 0.0 <= section_energy <= 1.0:
            raise ValueError("section_energy must be within 0..1")

        if candidate.realization is not None:
            self.piano.commit(candidate.realization)
            self.recent_density = blend_density(
                self.recent_density,
                self._estimate_density(candidate),
            )
            self.sounding_streak += 1
            self.silence_streak = 0
            self.last_family = candidate.realization.event.source_family
        else:
            self.recent_density = decay_density(self.recent_density)
            self.silence_streak += 1
            self.sounding_streak = 0
            self.last_family = None

        self.last_role = candidate.role.value
        self.recent_signatures.append(GestureSignature.from_candidate(candidate))
        if len(self.recent_signatures) > 8:
            del self.recent_signatures[:-8]
        if section_energy is not None:
            self.last_section_energy = section_energy
        self.committed.append(candidate)

    def observe_harmonic_frame(
        self,
        frame: HarmonicFrame,
    ) -> HarmonicContinuityFeatures:
        features = self.harmonic_continuity.observe(frame)
        self.last_harmonic_continuity = features
        return features

    def effective_pattern_consistency(
        self,
        context: PianoCompingContext,
    ) -> float:
        if context.auto_pattern_consistency and self.last_harmonic_continuity is not None:
            return self.last_harmonic_continuity.pattern_consistency_strength
        return context.pattern_consistency_strength

    def record_ensemble_response(
        self,
        observation: EnsembleResponseObservation,
    ) -> None:
        observation.validate()
        if not self.recent_signatures:
            raise ValueError("cannot attribute ensemble response without a committed gesture")
        self.recent_responses.append(
            GestureResponseRecord(self.recent_signatures[-1], observation)
        )
        if len(self.recent_responses) > 8:
            del self.recent_responses[:-8]
        self.active_episode = infer_interaction_episode(self.recent_responses)

    def observe_context_transition(
        self,
        before: PianoCompingContext,
        after: PianoCompingContext,
        *,
        latency_beats: float = 0.5,
        attribution_confidence: float = 0.25,
    ) -> tuple[EnsembleResponseObservation, ...]:
        if not self.recent_signatures:
            raise ValueError("cannot observe response transition before a committed gesture")
        observations = infer_coarse_responses(
            EnsembleSnapshot.from_context(before),
            EnsembleSnapshot.from_context(after),
            latency_beats=latency_beats,
            attribution_confidence=attribution_confidence,
        )
        for observation in observations:
            self.record_ensemble_response(observation)
        return observations

    def interaction_state_from_context(
        self,
        context: PianoCompingContext,
    ) -> PianoInteractionState:
        context.validate()
        phrase_space = None
        if context.available_space_beats > 0:
            phrase_space = PhraseSpaceWindow(
                confidence=context.phrase_boundary_probability,
                estimated_length_beats=context.available_space_beats,
                source="comping_context",
            )

        return PianoInteractionState(
            soloist_activity=context.soloist_activity,
            ensemble_density=context.ensemble_density,
            recent_piano_density=self.recent_density,
            phrase_space=phrase_space,
            section_energy=context.section_energy,
            energy_direction=infer_energy_direction(
                self.last_section_energy,
                context.section_energy,
            ),
        )


class PianoCompingEvaluator:
    """Contextual policy above the shared harmony and piano realization layers."""

    def __init__(self, piano_evaluator: PianoPolicyEvaluator | None = None):
        self.piano_evaluator = piano_evaluator or PianoPolicyEvaluator()

    @staticmethod
    def _add(
        score: float,
        components: dict[str, float],
        reasons: list[str],
        key: str,
        value: float,
        reason: str,
    ) -> float:
        score += value
        components[key] = components.get(key, 0.0) + value
        reasons.append(reason)
        return score

    def evaluate(
        self,
        candidate: PianoCompingCandidate,
        comping_context: PianoCompingContext,
        musical_context: MusicalContextVector,
        state: PianoCompingState,
        harmonic_affordance: HarmonicAffordance | None = None,
        interaction_state: PianoInteractionState | None = None,
        harmonic_reasoning: HarmonicReasoningResult | None = None,
    ) -> PianoCompingScore:
        candidate.validate()
        comping_context.validate()

        score = 0.0
        components: dict[str, float] = {}
        reasons: list[str] = []
        piano_score: PianoActionScore | None = None

        foreground_activity = comping_context.soloist_activity
        if comping_context.ensemble_mode in {
            PianoEnsembleMode.PIANO_HEAD_TRIO,
            PianoEnsembleMode.PIANO_SOLO_TRIO,
        }:
            foreground_activity = max(
                foreground_activity,
                comping_context.piano_foreground_activity,
            )
        busy_solo = foreground_activity >= 0.72
        phrase_open = comping_context.phrase_boundary_probability >= 0.65
        useful_space = comping_context.available_space_beats >= 0.5
        crowded = comping_context.ensemble_density >= 0.72
        piano_recently_busy = comping_context.recent_piano_density >= 0.65

        if candidate.action_type is CompingActionType.SILENCE:
            if busy_solo:
                score = self._add(
                    score, components, reasons, "solo_space", 0.28,
                    "silence yields to active soloist",
                )
            if crowded:
                score = self._add(
                    score, components, reasons, "ensemble_space", 0.16,
                    "silence reduces ensemble crowding",
                )
            if piano_recently_busy:
                score = self._add(
                    score, components, reasons, "self_density_release", 0.14,
                    "silence releases recent piano density",
                )
            if phrase_open and useful_space and candidate.role in {
                InteractionRole.ANSWER,
                InteractionRole.FILL,
            }:
                score = self._add(
                    score, components, reasons, "missed_response_window", -0.18,
                    "available phrase-space supports a response candidate",
                )
            if candidate.role is InteractionRole.LAY_OUT:
                score = self._add(
                    score, components, reasons, "role_fit", 0.16,
                    "silence directly realizes lay-out intention",
                )
        else:
            assert candidate.realization is not None
            piano_score = self.piano_evaluator.evaluate(
                candidate.realization,
                musical_context,
                state.piano,
            )
            score += piano_score.total
            components.update(piano_score.components)
            reasons.extend(piano_score.reasons)

            hands = dict(candidate.realization.hand_assignment)
            piano_foreground = comping_context.ensemble_mode in {
                PianoEnsembleMode.PIANO_HEAD_TRIO,
                PianoEnsembleMode.PIANO_SOLO_TRIO,
            }
            if piano_foreground:
                # In a piano-led trio the RH owns melody/solo foreground. Comping
                # should normally be a LH function; RH chordal occupation competes
                # with the line unless explicitly realized as a two-hand texture.
                if any(hand == "RH" for hand in hands.values()):
                    score = self._add(
                        score, components, reasons,
                        "foreground_hand_contract", -0.34,
                        "RH is reserved for melody/solo foreground in piano-led trio mode",
                    )
                elif hands and all(hand == "LH" for hand in hands.values()):
                    score = self._add(
                        score, components, reasons,
                        "left_hand_comping_fit", 0.12,
                        "LH-only comping supports RH foreground ownership",
                    )
                if candidate.action_type is CompingActionType.SUSTAINED_SUPPORT:
                    score = self._add(
                        score, components, reasons,
                        "foreground_sustain_restraint", -0.05,
                        "continuous LH sustain can make piano-trio solo texture too static",
                    )

            lh_texture_bias = evaluate_lh_texture_bias(
                candidate,
                comping_context,
            )
            score += lh_texture_bias.score_delta
            for key, value in lh_texture_bias.components.items():
                components[key] = components.get(key,0.0) + value
            reasons.extend(lh_texture_bias.reasons)

            lh_voice_leading_bias = evaluate_lh_voice_leading(
                candidate,
                state,
            )
            score += lh_voice_leading_bias.score_delta
            for key, value in lh_voice_leading_bias.components.items():
                components[key] = components.get(key,0.0) + value
            reasons.extend(lh_voice_leading_bias.reasons)

            rh_lh_bias = evaluate_rh_lh_interaction(
                candidate,
                comping_context,
            )
            score += rh_lh_bias.score_delta
            for key, value in rh_lh_bias.components.items():
                components[key] = components.get(key,0.0) + value
            reasons.extend(rh_lh_bias.reasons)

            event = candidate.realization.event
            if harmonic_reasoning is not None:
                guidance = harmonic_guidance_for_candidate(event, harmonic_reasoning)
                score += guidance.score_delta
                for key, value in guidance.components.items():
                    components[f"shared_{key}"] = components.get(
                        f"shared_{key}", 0.0
                    ) + value
                if guidance.score_delta:
                    components["shared_harmonic_guidance_total"] = guidance.score_delta
                reasons.extend(guidance.reasons)
            sparse = "sparse" in event.tags or candidate.action_type is CompingActionType.SPARSE_SUPPORT
            dense = "dense" in event.tags

            if busy_solo and dense:
                score = self._add(
                    score, components, reasons, "solo_intrusion", -0.22,
                    "dense sounding gesture risks masking active soloist",
                )
            if busy_solo and sparse and candidate.role is InteractionRole.SUPPORT:
                score = self._add(
                    score, components, reasons, "restrained_support", 0.08,
                    "sparse support can coexist with active soloist",
                )

            if phrase_open and useful_space and candidate.role in {
                InteractionRole.ANSWER,
                InteractionRole.FILL,
                InteractionRole.PUNCTUATE,
            }:
                score = self._add(
                    score, components, reasons, "phrase_space_fit", 0.24,
                    "gesture uses a likely phrase-space window",
                )

            rhythm_tags = {tag for tag in candidate.tags if tag.startswith("rhythm:")}

            if candidate.action_type is CompingActionType.PUNCTUATION:
                if comping_context.drummer_activity >= 0.65:
                    score = self._add(
                        score, components, reasons, "rhythmic_dialogue", 0.08,
                        "punctuation can participate in active rhythmic dialogue",
                    )
                if candidate.duration_beats > 1.0:
                    score = self._add(
                        score, components, reasons, "punctuation_length", -0.08,
                        "long duration weakens punctuation character",
                    )
                if comping_context.drummer_activity >= 0.65 and (
                    "rhythm:anticipated" in rhythm_tags
                    or "rhythm:offbeat" in rhythm_tags
                ):
                    score = self._add(
                        score, components, reasons, "rhythmic_placement_fit", 0.05,
                        "anticipated/offbeat punctuation fits active rhythmic dialogue",
                    )

            if (
                candidate.role is InteractionRole.ANSWER
                and phrase_open
                and useful_space
                and "rhythm:delayed" in rhythm_tags
            ):
                score = self._add(
                    score, components, reasons, "delayed_answer_fit", 0.08,
                    "delayed placement fits a phrase-space answer",
                )

            if (
                candidate.action_type is CompingActionType.SUSTAINED_SUPPORT
                and "rhythm:sustained" in rhythm_tags
                and not busy_solo
            ):
                score = self._add(
                    score, components, reasons, "sustained_support_fit", 0.04,
                    "sustained placement fits available accompaniment space",
                )

            family_tags = set(event.tags) | set(candidate.tags)

            if {"extension", "color_tone", "tension"} & family_tags:
                color_bonus = 0.07 * comping_context.tension_preference
                score = self._add(
                    score, components, reasons,
                    "color_tension_preference", color_bonus,
                    "piano comping favors a moderate amount of extension/color",
                )

            if "high_tension" in family_tags:
                if busy_solo or crowded:
                    score = self._add(
                        score, components, reasons,
                        "altered_tension_restraint", -0.05,
                        "strong altered tension is restrained when foreground/ensemble is busy",
                    )
                else:
                    score = self._add(
                        score, components, reasons,
                        "altered_tension_color", 0.025 * comping_context.tension_preference,
                        "explicit Core-supplied altered color can enrich open comping space",
                    )

            if interaction_state is not None:
                if (
                    interaction_state.energy_direction is EnergyDirection.UP
                    and "register:higher" in family_tags
                ):
                    score = self._add(
                        score, components, reasons, "register_energy_fit", 0.05,
                        "higher register supports current rising-energy option",
                    )
                if (
                    interaction_state.energy_direction is EnergyDirection.DOWN
                    and "dynamic:soft" in family_tags
                ):
                    score = self._add(
                        score, components, reasons, "dynamic_release_fit", 0.05,
                        "soft dynamic supports falling-energy option",
                    )

            if busy_solo or crowded:
                if "dynamic:soft" in family_tags:
                    score = self._add(
                        score, components, reasons, "dynamic_space_fit", 0.05,
                        "soft dynamic reduces masking in a busy ensemble",
                    )
                if "dynamic:strong" in family_tags:
                    score = self._add(
                        score, components, reasons, "dynamic_masking", -0.07,
                        "strong dynamic risks masking a busy ensemble",
                    )

            if candidate.role in {InteractionRole.PUNCTUATE, InteractionRole.ANCHOR}:
                if "touch:percussive" in family_tags:
                    score = self._add(
                        score, components, reasons, "touch_role_fit", 0.04,
                        "percussive touch supports punctuation/anchor definition",
                    )

            if candidate.role in {InteractionRole.SUPPORT, InteractionRole.RELEASE}:
                if "touch:legato" in family_tags and not busy_solo:
                    score = self._add(
                        score, components, reasons, "touch_support_fit", 0.03,
                        "legato touch supports sustained/releasing accompaniment",
                    )

            if comping_context.soloist_register_midi is not None:
                center = sum(event.pitches_midi) / len(event.pitches_midi)
                distance = abs(center - comping_context.soloist_register_midi)
                if distance < 5:
                    score = self._add(
                        score, components, reasons, "register_collision", -0.08,
                        "piano register closely overlaps soloist register",
                    )
                elif distance >= 12:
                    score = self._add(
                        score, components, reasons, "register_separation", 0.03,
                        "piano register leaves clearer separation from soloist",
                    )

            if candidate.role is InteractionRole.SUPPORT and "shell" in family_tags:
                if busy_solo or comping_context.ensemble_density >= 0.6:
                    score = self._add(
                        score, components, reasons, "shell_support_fit", 0.08,
                        "shell voicing supports restrained accompaniment",
                    )

            if candidate.role is InteractionRole.ANSWER and "rootless" in family_tags:
                if phrase_open and useful_space:
                    score = self._add(
                        score, components, reasons, "rootless_answer_fit", 0.08,
                        "rootless color can serve a phrase-space response",
                    )

            if candidate.role is InteractionRole.BUILD:
                if comping_context.section_energy >= 0.55 and not busy_solo:
                    score = self._add(
                        score, components, reasons, "build_context", 0.10,
                        "section context can support an energy-building gesture",
                    )
                if "rootless" in family_tags:
                    score = self._add(
                        score, components, reasons, "rootless_build_fit", 0.06,
                        "rootless color supports a build candidate",
                    )
                if sparse:
                    score = self._add(
                        score, components, reasons, "build_density_mismatch", -0.06,
                        "very sparse gesture weakly realizes build intention",
                    )

            if candidate.role is InteractionRole.RELEASE and sparse:
                score = self._add(
                    score, components, reasons, "release_fit", 0.10,
                    "sparse gesture supports release intention",
                )

        previous_signature = (
            state.recent_signatures[-1] if state.recent_signatures else None
        )
        base_creative_profile = profile_from_harmonic_context(
            state.last_harmonic_continuity
        )
        creative_profile = adapt_continuity_profile_for_harmony(
            base_creative_profile,
            harmonic_reasoning,
        )
        creative_context = adapt_creativity_context_for_harmony(
            CreativityContext(
                creativity_strength=comping_context.creativity_strength,
                coherence_floor=comping_context.creativity_coherence_floor,
            ),
            harmonic_reasoning,
        )
        creative_bias = evaluate_creative_continuity(
            candidate,
            previous_signature,
            creative_profile,
            creative_context,
        )
        score += creative_bias.total
        for key, value in creative_bias.components.items():
            components[f"creative_continuity:{key}"] = components.get(
                f"creative_continuity:{key}", 0.0
            ) + value
        reasons.extend(creative_bias.reasons)

        occupancy_bias = evaluate_role_occupancy_bias(
            candidate,
            comping_context.role_occupancy,
        )
        score += occupancy_bias.total
        for key, value in occupancy_bias.components.items():
            components[f"role_occupancy:{key}"] = components.get(
                f"role_occupancy:{key}", 0.0
            ) + value
        reasons.extend(occupancy_bias.reasons)

        harmonic_turn_bias = evaluate_bebop_harmonic_turn_comping_bias(
            candidate,
            comping_context.harmonic_turn,
        )
        score += harmonic_turn_bias.total
        for key, value in harmonic_turn_bias.components.items():
            components[f"bebop_harmonic_turn:{key}"] = components.get(
                f"bebop_harmonic_turn:{key}", 0.0
            ) + value
        reasons.extend(harmonic_turn_bias.reasons)

        episode_bias = evaluate_episode_bias(candidate, state.active_episode)
        score += episode_bias.total
        for key, value in episode_bias.components.items():
            components[f"interaction_episode:{key}"] = components.get(
                f"interaction_episode:{key}", 0.0
            ) + value
        reasons.extend(episode_bias.reasons)

        response_bias = evaluate_response_bias(
            candidate,
            state.recent_responses,
        )
        score += response_bias.total
        for key, value in response_bias.components.items():
            components[f"ensemble_response:{key}"] = components.get(
                f"ensemble_response:{key}", 0.0
            ) + value
        reasons.extend(response_bias.reasons)

        variation = evaluate_variation(
            candidate,
            state.recent_signatures,
            VariationContext(
                variation_pressure=comping_context.variation_pressure,
                groove_lock_strength=comping_context.groove_lock_strength,
                motif_continuity_strength=comping_context.motif_continuity_strength,
                pattern_consistency_strength=state.effective_pattern_consistency(
                    comping_context
                ),
            ),
        )
        score += variation.total
        for key, value in variation.components.items():
            components[f"variation:{key}"] = components.get(f"variation:{key}", 0.0) + value
        reasons.extend(variation.reasons)

        if interaction_state is not None:
            narrative = evaluate_narrative_bias(candidate, interaction_state)
            score += narrative.total
            for key, value in narrative.components.items():
                components[f"narrative:{key}"] = components.get(f"narrative:{key}", 0.0) + value
            reasons.extend(narrative.reasons)

        if harmonic_affordance is not None:
            if (
                candidate.harmonic_affordance_id is not None
                and candidate.harmonic_affordance_id != harmonic_affordance.affordance_id
            ):
                score = self._add(
                    score, components, reasons, "affordance_mismatch", -0.30,
                    "candidate declares a different Core harmonic affordance",
                )
            elif candidate.harmonic_affordance_id == harmonic_affordance.affordance_id:
                score = self._add(
                    score, components, reasons, "affordance_alignment", 0.06,
                    "candidate realizes the supplied Core harmonic affordance",
                )

        return PianoCompingScore(
            candidate=candidate,
            total=score,
            components=components,
            reasons=tuple(reasons),
            piano_score=piano_score,
        )

    def choose_immediate(
        self,
        candidates: Sequence[PianoCompingCandidate],
        comping_context: PianoCompingContext,
        musical_context: MusicalContextVector,
        state: PianoCompingState,
        harmonic_affordance: HarmonicAffordance | None = None,
        interaction_state: PianoInteractionState | None = None,
        harmonic_reasoning: HarmonicReasoningResult | None = None,
    ) -> PianoCompingScore:
        if not candidates:
            raise ValueError("no comping candidates")
        return max(
            (
                self.evaluate(
                    candidate,
                    comping_context,
                    musical_context,
                    state,
                    harmonic_affordance,
                    interaction_state,
                    harmonic_reasoning,
                )
                for candidate in candidates
            ),
            key=lambda item: item.total,
        )


def perform_one_comping_action(
    plan: SoftPlan,
    evaluator: PianoCompingEvaluator,
    candidates: Sequence[PianoCompingCandidate],
    comping_context: PianoCompingContext,
    musical_context: MusicalContextVector,
    state: PianoCompingState,
    harmonic_affordance: HarmonicAffordance | None = None,
    interaction_state: PianoInteractionState | None = None,
    harmonic_frame: HarmonicFrame | None = None,
    harmonic_reasoning: HarmonicReasoningResult | None = None,
) -> PianoCompingScore:
    """Commit exactly one immediate comping decision, sounding or silent."""

    plan.validate_for_improvisation()
    if harmonic_frame is not None:
        state.observe_harmonic_frame(harmonic_frame)
    effective_interaction = (
        interaction_state
        if interaction_state is not None
        else state.interaction_state_from_context(comping_context)
    )
    chosen = evaluator.choose_immediate(
        candidates,
        comping_context,
        musical_context,
        state,
        harmonic_affordance,
        effective_interaction,
        harmonic_reasoning,
    )
    state.commit(chosen.candidate, section_energy=comping_context.section_energy)
    return chosen
