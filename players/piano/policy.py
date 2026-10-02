"""Piano-specific online performance policy.

The shared Core supplies musical context and the generic SoftPlan contract.
This module owns only piano-specific realization decisions.

Important runtime rule: a plan may prepare intentions and candidate families,
but this policy commits exactly one immediately playable piano action at a time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from music_intelligence.reasoning.online_improviser import SoftPlan


@dataclass(frozen=True)
class PianoVoicingCandidate:
    """One immediately playable polyphonic piano action."""

    pitches_midi: tuple[int, ...]
    duration_beats: float
    onset_offset_beats: float = 0.0
    velocity: int = 72
    tags: frozenset[str] = frozenset()
    role: str = "comping"
    source_family: str = "piano_generated"

    def validate(self) -> None:
        if not self.pitches_midi:
            raise ValueError("piano voicing must contain at least one pitch")
        if self.duration_beats <= 0:
            raise ValueError("duration_beats must be positive")
        if not 1 <= self.velocity <= 127:
            raise ValueError("velocity must be in MIDI range 1..127")
        if any(p < 21 or p > 108 for p in self.pitches_midi):
            raise ValueError("piano pitch outside acoustic-piano MIDI range")


@dataclass(frozen=True)
class PianoActionScore:
    candidate: PianoVoicingCandidate
    total: float
    components: Mapping[str, float] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()


@dataclass
class PianoPerformanceState:
    """Piano-local performed history; shared musical memory remains in Core."""

    last_voicing: tuple[int, ...] = ()
    committed: list[PianoVoicingCandidate] = field(default_factory=list)

    def commit(self, candidate: PianoVoicingCandidate) -> None:
        candidate.validate()
        self.last_voicing = candidate.pitches_midi
        self.committed.append(candidate)


def _nearest_voice_motion(previous: Sequence[int], current: Sequence[int]) -> float:
    if not previous or not current:
        return 0.0
    distances = [min(abs(p - q) for q in previous) for p in current]
    return sum(distances) / len(distances)


class PianoPolicyEvaluator:
    """Evaluate only unperformed, immediate piano candidates."""

    def evaluate(
        self,
        candidate: PianoVoicingCandidate,
        context: MusicalContextVector,
        state: PianoPerformanceState,
    ) -> PianoActionScore:
        candidate.validate()
        score = 0.0
        components: dict[str, float] = {}
        reasons: list[str] = []
        tags = set(candidate.tags)

        if {"guide_tones", "shell"} & tags:
            value = 0.20
            score += value
            components["harmonic_clarity"] = value
            reasons.append("preserves harmonic identity")

        if state.last_voicing:
            motion = _nearest_voice_motion(state.last_voicing, candidate.pitches_midi)
            if motion <= 3.0:
                value = 0.18
                reasons.append("economical voice leading")
            elif motion >= 8.0:
                value = -0.14
                reasons.append("large aggregate voice-leading motion")
            else:
                value = 0.0
            if value:
                score += value
                components["voice_leading"] = value

        busy_ensemble = context.ensemble_activity >= 0.65
        if busy_ensemble and {"leave_space", "sparse"} & tags:
            value = 0.24
            score += value
            components["ensemble_space"] = value
            reasons.append("yields space to active ensemble")
        if busy_ensemble and {"dense", "rhythmic_fill"} & tags:
            value = -0.22
            score += value
            components["density_fit"] = value
            reasons.append("avoids crowding an active ensemble")

        if "answer" in tags:
            value = 0.12
            score += value
            components["interaction"] = value
            reasons.append("supports call-and-response behavior")

        if "anticipation" in tags and candidate.onset_offset_beats < 0:
            value = 0.10
            score += value
            components["anticipation"] = value
            reasons.append("controlled harmonic/rhythmic anticipation")

        if context.tension >= 0.7 and {"upper_structure", "altered_color"} & tags:
            value = 0.10
            score += value
            components["tension_fit"] = value
            reasons.append("color matches elevated tension")

        if context.tension <= 0.3 and "high_tension_cluster" in tags:
            value = -0.12
            score += value
            components["tension_mismatch"] = value
            reasons.append("avoids premature harmonic density")

        return PianoActionScore(candidate, score, components, tuple(reasons))

    def choose_immediate(
        self,
        candidates: Sequence[PianoVoicingCandidate],
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
    candidates: Sequence[PianoVoicingCandidate],
    context: MusicalContextVector,
    state: PianoPerformanceState,
) -> PianoActionScore:
    """Commit one piano action, then return control to the listen/re-plan loop."""

    plan.validate_for_improvisation()
    chosen = evaluator.choose_immediate(candidates, context, state)
    state.commit(chosen.candidate)
    return chosen
