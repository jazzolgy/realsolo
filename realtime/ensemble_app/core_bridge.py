from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from music_intelligence.reasoning.legend_style_core import CandidateEvent, MusicalContextVector
from music_intelligence.reasoning.online_improviser import (
    OnlineMusicalEvaluator,
    PerformanceMemory,
    SoftPlan,
    perform_one_event,
)

from .models import EnsembleState, MusicalAction


class CandidateFactory(Protocol):
    """Realtime supplies evidence; candidate meaning/grammar belongs outside the scheduler."""

    def build(
        self, state: EnsembleState, trigger: str
    ) -> tuple[SoftPlan, Sequence[CandidateEvent], MusicalContextVector]: ...


@dataclass
class CoreImmediateBridge:
    """Adapter from live EnsembleState to the shared v1.30 one-event Core contract."""

    factory: CandidateFactory
    evaluator: OnlineMusicalEvaluator
    memory: PerformanceMemory

    def decide(self, state: EnsembleState, trigger: str) -> tuple[MusicalAction, ...]:
        plan, candidates, context = self.factory.build(state, trigger)
        if not candidates:
            return ()
        chosen = perform_one_event(plan, self.evaluator, candidates, context, self.memory)
        event = chosen.candidate
        if event.pitch_midi is None:
            return ()

        beat_s = state.beat.beat_period_s or 0.5
        duration_s = max(0.03, event.duration_beats * beat_s)
        delay_s = max(0.0, event.onset_offset_beats * beat_s)
        reason = "; ".join(chosen.reasons) or "core immediate choice"
        velocity = int(max(1, min(127, 34 + state.human_activity * 54)))
        return (MusicalAction(event.pitch_midi, velocity, duration_s, delay_s, reason=reason),)


class DiagnosticResponseFactory:
    """Hardware/closed-loop probe, not final accompaniment intelligence.

    It offers Core only two immediate candidates after a detected phrase ending:
    a clearly audible octave-down response to prove perception-to-output closure,
    or silence. No future phrase is scripted.
    """

    def build(self, state: EnsembleState, trigger: str):
        plan = SoftPlan(
            horizon_beats=1.0,
            intention="verify listen-decide-commit-listen loop",
            soft_targets=("respond only after phrase space",),
            candidate_families=("diagnostic_response", "space"),
        )
        context = MusicalContextVector(
            metric_position=state.beat.phase or 0.0,
            phrase_maturity=1.0 if state.phrase.phrase_end else 0.5,
            ensemble_activity=state.human_activity,
        )
        if trigger != "phrase_end" or state.phrase.last_pitch is None:
            return plan, (CandidateEvent(None, 0.25, tags=frozenset({"ensemble_space"})),), context

        response_pitch = max(21, min(108, state.phrase.last_pitch - 12))
        # Response and silence are both legal; the shared evaluator performs the immediate choice.
        candidates = (
            CandidateEvent(response_pitch, 0.45, tags=frozenset({"response_probe"}), source_family="diagnostic"),
            CandidateEvent(None, 0.45, tags=frozenset({"ensemble_space"}), source_family="diagnostic"),
        )
        return plan, candidates, context
