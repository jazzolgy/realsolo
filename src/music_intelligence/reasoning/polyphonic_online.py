"""Online handling for one immediate polyphonic action.

A sonority is one atomic current action: choose one candidate, commit it,
then listen/re-plan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .legend_style_core import MusicalContextVector
from .online_improviser import SoftPlan
from .polyphonic_event import PolyphonicEventCandidate


@dataclass(frozen=True)
class PolyphonicCandidateScore:
    candidate: PolyphonicEventCandidate
    total: float
    components: Mapping[str, float] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()


@dataclass
class PolyphonicPerformanceMemory:
    committed: list[PolyphonicEventCandidate] = field(default_factory=list)

    def commit(self, event: PolyphonicEventCandidate) -> None:
        event.validate()
        self.committed.append(event)

    @property
    def last_event(self) -> PolyphonicEventCandidate | None:
        return self.committed[-1] if self.committed else None


def _voice_motion(previous: PolyphonicEventCandidate, current: PolyphonicEventCandidate) -> float | None:
    prev = {v.voice_id: v.pitch_midi for v in previous.voices}
    pairs = [
        abs(v.pitch_midi - prev[v.voice_id])
        for v in current.voices
        if v.voice_id in prev
    ]
    if not pairs:
        return None
    return sum(pairs) / len(pairs)


class PolyphonicOnlineEvaluator:
    """Instrument-neutral evaluation of immediate sonority candidates."""

    def evaluate(
        self,
        candidate: PolyphonicEventCandidate,
        context: MusicalContextVector,
        memory: PolyphonicPerformanceMemory,
    ) -> PolyphonicCandidateScore:
        candidate.validate()
        score = 0.0
        components: dict[str, float] = {}
        reasons: list[str] = []

        previous = memory.last_event
        if previous is not None:
            motion = _voice_motion(previous, candidate)
            if motion is not None:
                if motion <= 3.0:
                    value = 0.12
                    reasons.append("economical identity-aware voice leading")
                elif motion >= 9.0:
                    value = -0.10
                    reasons.append("large aggregate voice motion")
                else:
                    value = 0.0
                if value:
                    score += value
                    components["voice_leading"] = value

        if candidate.top_note_constraint is not None:
            top = max(candidate.pitches_midi)
            c = candidate.top_note_constraint
            satisfied = True
            if c.target_pitch_midi is not None:
                satisfied = satisfied and top == c.target_pitch_midi
            if c.target_pitch_class is not None:
                satisfied = satisfied and top % 12 == c.target_pitch_class
            if c.voice_id is not None:
                by_id = {v.voice_id: v.pitch_midi for v in candidate.voices}
                satisfied = satisfied and by_id[c.voice_id] == top
            value = 0.10 if satisfied else (-0.20 if c.required else -0.04)
            score += value
            components["top_line"] = value
            reasons.append("top-line constraint satisfied" if satisfied else "top-line constraint conflict")

        if candidate.bass_relation is not None:
            bass_id = candidate.bass_relation.bass_voice_id
            by_id = {v.voice_id: v.pitch_midi for v in candidate.voices}
            if by_id[bass_id] == min(candidate.pitches_midi):
                value = 0.06
                score += value
                components["bass_identity"] = value
                reasons.append("declared bass voice is registrally lowest")

        if candidate.doublings:
            value = 0.02
            score += value
            components["explicit_doubling_semantics"] = value
            reasons.append("doubling semantics are explicit")

        if context.ensemble_activity >= .70 and "sparse" in candidate.tags:
            value = 0.12
            score += value
            components["ensemble_space"] = value
            reasons.append("sparse texture yields to active ensemble")
        if context.ensemble_activity >= .70 and "dense" in candidate.tags:
            value = -0.12
            score += value
            components["density_fit"] = value
            reasons.append("dense texture risks crowding active ensemble")

        return PolyphonicCandidateScore(candidate, score, components, tuple(reasons))

    def choose_immediate(
        self,
        candidates: Sequence[PolyphonicEventCandidate],
        context: MusicalContextVector,
        memory: PolyphonicPerformanceMemory,
    ) -> PolyphonicCandidateScore:
        if not candidates:
            raise ValueError("no polyphonic candidates")
        return max(
            (self.evaluate(candidate, context, memory) for candidate in candidates),
            key=lambda item: item.total,
        )


def perform_one_polyphonic_event(
    plan: SoftPlan,
    evaluator: PolyphonicOnlineEvaluator,
    candidates: Sequence[PolyphonicEventCandidate],
    context: MusicalContextVector,
    memory: PolyphonicPerformanceMemory,
) -> PolyphonicCandidateScore:
    """Commit one immediate sonority, then return to the listen/re-plan loop."""
    plan.validate_for_improvisation()
    chosen = evaluator.choose_immediate(candidates, context, memory)
    memory.commit(chosen.candidate)
    return chosen
