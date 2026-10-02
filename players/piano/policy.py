"""Piano-specific online realization policy.

Shared sonority semantics and generic polyphonic evaluation live in Core.
This module adds only piano-specific feasibility and realization choices.

Runtime contract:
- plan intention, not exact future notes
- choose one immediate polyphonic gesture
- realize it for piano
- commit once
- listen and re-plan
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from music_intelligence.reasoning.online_improviser import SoftPlan
from music_intelligence.reasoning.polyphonic_event import PolyphonicEventCandidate
from music_intelligence.reasoning.polyphonic_online import (
    PolyphonicCandidateScore,
    PolyphonicOnlineEvaluator,
    PolyphonicPerformanceMemory,
)


PIANO_LOW_MIDI = 21
PIANO_HIGH_MIDI = 108


@dataclass(frozen=True)
class PianoRealizationCandidate:
    """Piano realization metadata wrapped around one shared Core gesture."""

    event: PolyphonicEventCandidate
    hand_assignment: tuple[tuple[str, str], ...] = ()
    pedal: str = "none"
    touch: str = "neutral"

    def validate(self) -> None:
        self.event.validate()

        if any(
            pitch < PIANO_LOW_MIDI or pitch > PIANO_HIGH_MIDI
            for pitch in self.event.pitches_midi
        ):
            raise ValueError("voice outside acoustic-piano MIDI range")

        known = {voice.voice_id for voice in self.event.voices}
        assigned: set[str] = set()
        for voice_id, hand in self.hand_assignment:
            if voice_id not in known:
                raise ValueError("hand assignment references unknown voice_id")
            if voice_id in assigned:
                raise ValueError("voice may not be assigned to more than one hand")
            if hand not in {"LH", "RH"}:
                raise ValueError("hand must be LH or RH")
            assigned.add(voice_id)

        if self.pedal not in {"none", "sustain", "half", "flutter", "sostenuto"}:
            raise ValueError("unsupported piano pedal mode")


@dataclass(frozen=True)
class PianoActionScore:
    candidate: PianoRealizationCandidate
    total: float
    components: Mapping[str, float] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()


@dataclass
class PianoPerformanceState:
    """Piano-local realization history plus shared polyphonic performance memory."""

    polyphonic_memory: PolyphonicPerformanceMemory = field(
        default_factory=PolyphonicPerformanceMemory
    )
    committed: list[PianoRealizationCandidate] = field(default_factory=list)

    def commit(self, candidate: PianoRealizationCandidate) -> None:
        candidate.validate()
        self.polyphonic_memory.commit(candidate.event)
        self.committed.append(candidate)


class PianoPolicyEvaluator:
    """Add piano-specific evaluation on top of the shared Core evaluator."""

    def __init__(self, core_evaluator: PolyphonicOnlineEvaluator | None = None):
        self.core_evaluator = core_evaluator or PolyphonicOnlineEvaluator()

    def _score_piano_realization(
        self,
        candidate: PianoRealizationCandidate,
        context: MusicalContextVector,
    ) -> tuple[float, dict[str, float], list[str]]:
        event = candidate.event
        score = 0.0
        components: dict[str, float] = {}
        reasons: list[str] = []

        pitches = event.pitches_midi
        span = max(pitches) - min(pitches)

        # Piano-specific physical/registral plausibility. This is deliberately
        # not a generic Core voicing judgment.
        if span > 36 and not candidate.hand_assignment:
            value = -0.12
            score += value
            components["piano_unassigned_wide_span"] = value
            reasons.append("wide piano span needs explicit hand realization")

        hands = dict(candidate.hand_assignment)
        if hands:
            by_id = {voice.voice_id: voice.pitch_midi for voice in event.voices}
            lh = [by_id[v] for v, hand in hands.items() if hand == "LH"]
            rh = [by_id[v] for v, hand in hands.items() if hand == "RH"]
            if lh and rh and max(lh) > min(rh) + 7:
                value = -0.10
                score += value
                components["hand_crossing_pressure"] = value
                reasons.append("large hand crossing pressure")

        if candidate.pedal in {"sustain", "half"} and context.ensemble_activity >= 0.8:
            if "dense" in event.tags:
                value = -0.08
                score += value
                components["pedal_texture_fit"] = value
                reasons.append("dense sustained piano texture may cloud active ensemble")

        if candidate.touch == "percussive" and "sparse" in event.tags:
            value = 0.03
            score += value
            components["touch_definition"] = value
            reasons.append("defined attack supports sparse piano gesture")

        return score, components, reasons

    def evaluate(
        self,
        candidate: PianoRealizationCandidate,
        context: MusicalContextVector,
        state: PianoPerformanceState,
    ) -> PianoActionScore:
        candidate.validate()

        core_score: PolyphonicCandidateScore = self.core_evaluator.evaluate(
            candidate.event,
            context,
            state.polyphonic_memory,
        )
        piano_score, piano_components, piano_reasons = self._score_piano_realization(
            candidate,
            context,
        )

        components = dict(core_score.components)
        components.update(piano_components)
        return PianoActionScore(
            candidate=candidate,
            total=core_score.total + piano_score,
            components=components,
            reasons=core_score.reasons + tuple(piano_reasons),
        )

    def choose_immediate(
        self,
        candidates: Sequence[PianoRealizationCandidate],
        context: MusicalContextVector,
        state: PianoPerformanceState,
    ) -> PianoActionScore:
        if not candidates:
            raise ValueError("no piano candidates")
        return max(
            (self.evaluate(candidate, context, state) for candidate in candidates),
            key=lambda item: item.total,
        )


def perform_one_piano_action(
    plan: SoftPlan,
    evaluator: PianoPolicyEvaluator,
    candidates: Sequence[PianoRealizationCandidate],
    context: MusicalContextVector,
    state: PianoPerformanceState,
) -> PianoActionScore:
    """Commit one piano realization of one shared Core gesture."""

    plan.validate_for_improvisation()
    chosen = evaluator.choose_immediate(candidates, context, state)
    state.commit(chosen.candidate)
    return chosen
