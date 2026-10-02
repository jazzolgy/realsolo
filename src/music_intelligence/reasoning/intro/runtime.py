"""Online Shared Intro Intelligence runtime."""
from __future__ import annotations

from dataclasses import dataclass, replace

from .classifier import update_intro_mode_hypotheses
from .cue_detector import update_entry_permission
from .entry_predictor import make_entry_decision, update_entry_readiness
from .policy import choose_entry_action
from .pulse_tracker import update_pulse_state
from .representation import EntryAction, EntryDecision, IntroObservation, IntroPhase, IntroState


@dataclass(frozen=True)
class IntroTickResult:
    state: IntroState
    decision: EntryDecision

    def validate(self) -> None:
        self.state.validate()
        self.decision.validate()


class IntroRuntime:
    """Consumes one observation and emits at most one shared entry action.

    The runtime never pre-composes an intro or future note sequence. After every
    tick the system must listen again before making another commitment.
    """

    def __init__(self, state: IntroState | None = None):
        self._state = state or IntroState()
        self._state.validate()

    @property
    def state(self) -> IntroState:
        return self._state

    def tick(self, observation: IntroObservation) -> IntroTickResult:
        observation.validate()
        if (
            self._state.last_timestamp is not None
            and observation.timestamp < self._state.last_timestamp
        ):
            raise ValueError("intro observations must be time-ordered")

        state = self._state
        if state.phase is IntroPhase.PRE_START:
            state = replace(
                state,
                phase=IntroPhase.INTRO_LISTENING,
                generation=state.generation + 1,
                provenance=state.provenance + ("intro_started",),
            )

        state = update_intro_mode_hypotheses(state, observation)
        state = update_pulse_state(state, observation)
        state = update_entry_permission(state, observation)
        state = update_entry_readiness(state, observation)

        decision = choose_entry_action(state, make_entry_decision(state))
        phase = _phase_for(state, decision)
        state = replace(
            state,
            phase=phase,
            generation=state.generation + 1,
            provenance=state.provenance + (f"entry_action:{decision.action.value}",),
        )

        self._state = state
        result = IntroTickResult(state, decision)
        result.validate()
        return result

    def handoff_to_normal_runtime(self) -> IntroState:
        """Mark the shared transition complete after the committed entry plays."""

        if self._state.phase is not IntroPhase.ENTRY_COMMITTED:
            raise ValueError("normal runtime handoff requires ENTRY_COMMITTED")
        self._state = replace(
            self._state,
            phase=IntroPhase.NORMAL_ENSEMBLE_RUNTIME,
            generation=self._state.generation + 1,
            provenance=self._state.provenance + ("normal_runtime_handoff",),
        )
        return self._state


def _phase_for(state: IntroState, decision: EntryDecision) -> IntroPhase:
    if decision.action is EntryAction.FULL_JOIN:
        return IntroPhase.ENTRY_COMMITTED
    if decision.action is EntryAction.PARTIAL_JOIN:
        return IntroPhase.ENTRY_PENDING
    if decision.action in {EntryAction.SHADOW, EntryAction.LIGHT_SUPPORT}:
        return IntroPhase.ENTRY_NEGOTIATION
    return IntroPhase.INTRO_LISTENING
