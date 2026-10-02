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
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.available_space_beats < 0:
            raise ValueError("available_space_beats cannot be negative")


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

    def commit(self, candidate: PianoCompingCandidate) -> None:
        candidate.validate()
        if candidate.realization is not None:
            self.piano.commit(candidate.realization)
        self.committed.append(candidate)


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

            if candidate.role is InteractionRole.BUILD:
                if comping_context.section_energy >= 0.55 and not busy_solo:
                    score = self._add(
                        score, components, reasons, "build_context", 0.10,
                        "section context can support an energy-building gesture",
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
) -> PianoCompingScore:
    """Commit exactly one immediate comping decision, sounding or silent."""

    plan.validate_for_improvisation()
    chosen = evaluator.choose_immediate(
        candidates,
        comping_context,
        musical_context,
        state,
        harmonic_affordance,
    )
    state.commit(chosen.candidate)
    return chosen
