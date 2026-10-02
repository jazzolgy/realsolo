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

from music_intelligence.harmony.jazz_harmony_core import HarmonicAffordance
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from music_intelligence.reasoning.online_improviser import SoftPlan

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
    time_feel: str = "swing"

    def validate(self) -> None:
        for name in (
            "soloist_activity",
            "phrase_boundary_probability",
            "bass_activity",
            "drummer_activity",
            "ensemble_density",
            "recent_piano_density",
            "section_energy",
            "variation_pressure",
            "groove_lock_strength",
            "motif_continuity_strength",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.available_space_beats < 0:
            raise ValueError("available_space_beats cannot be negative")
        if self.soloist_register_midi is not None and not 0 <= self.soloist_register_midi <= 127:
            raise ValueError("soloist_register_midi must be within MIDI range")


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
    ) -> PianoCompingScore:
        candidate.validate()
        comping_context.validate()

        score = 0.0
        components: dict[str, float] = {}
        reasons: list[str] = []
        piano_score: PianoActionScore | None = None

        busy_solo = comping_context.soloist_activity >= 0.72
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

            event = candidate.realization.event
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
) -> PianoCompingScore:
    """Commit exactly one immediate comping decision, sounding or silent."""

    plan.validate_for_improvisation()
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
    )
    state.commit(chosen.candidate, section_energy=comping_context.section_energy)
    return chosen
