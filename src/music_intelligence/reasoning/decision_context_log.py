"""Decision/context logging for causal one-event runtime reasoning.

This module records what the system knew, what candidates were considered, and
what was committed. It deliberately does not score post-event musical quality
or update long-term learning. Logged data may later support offline analysis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .ensemble_state import EnsembleState


@dataclass(frozen=True)
class EnsembleContextSnapshot:
    generation: int
    beat: float
    bar: int
    section: str
    chorus: int
    form_position: float
    ensemble_density: float
    ensemble_energy: float
    ensemble_tension: float
    space_available: float
    leader_player_id: str | None
    active_player_ids: tuple[str, ...]
    recent_interaction_count: int
    harmonic_state_id: str | None
    groove_grammar_id: str = ""
    groove_confidence: float | None = None


def snapshot_ensemble_context(state: EnsembleState) -> EnsembleContextSnapshot:
    state.validate()
    groove=state.groove
    return EnsembleContextSnapshot(
        generation=state.generation,
        beat=state.transport.beat,
        bar=state.transport.bar,
        section=state.transport.section,
        chorus=state.transport.chorus,
        form_position=state.transport.form_position,
        ensemble_density=state.ensemble_density,
        ensemble_energy=state.ensemble_energy,
        ensemble_tension=state.ensemble_tension,
        space_available=state.space_available,
        leader_player_id=state.leader_player_id,
        active_player_ids=tuple(p.player_id for p in state.active_players()),
        recent_interaction_count=len(state.recent_interactions),
        harmonic_state_id=state.harmonic_state_id,
        groove_grammar_id=groove.grammar_id if groove is not None else "",
        groove_confidence=groove.confidence if groove is not None else None,
    )


@dataclass(frozen=True)
class CandidateAudit:
    candidate_id: str
    total_score: float
    components: Mapping[str, float] = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    descriptor: Mapping[str, str | float | int | bool | None] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id is required")


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    player_id: str
    decision_kind: str
    context: EnsembleContextSnapshot | None
    candidates: tuple[CandidateAudit, ...]
    selected_candidate_id: str
    selected_score: float
    prior_contributions: Mapping[str, float] = field(default_factory=dict)
    contextual_gate_weights: Mapping[str, float] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.decision_id:
            raise ValueError("decision_id is required")
        if not self.player_id:
            raise ValueError("player_id is required")
        if not self.decision_kind:
            raise ValueError("decision_kind is required")
        if not self.candidates:
            raise ValueError("decision record requires candidate audit entries")
        for candidate in self.candidates:
            candidate.validate()
        ids={candidate.candidate_id for candidate in self.candidates}
        if self.selected_candidate_id not in ids:
            raise ValueError("selected candidate must exist in candidate audit entries")


@dataclass(frozen=True)
class PostEventObservation:
    decision_id: str
    context: EnsembleContextSnapshot
    observed_event_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.decision_id:
            raise ValueError("decision_id is required")


@dataclass
class DecisionContextLog:
    """Append-only runtime audit log, not a learning engine."""

    decisions: list[DecisionRecord] = field(default_factory=list)
    post_event_observations: list[PostEventObservation] = field(default_factory=list)

    def append_decision(self, record: DecisionRecord) -> None:
        record.validate()
        self.decisions.append(record)

    def append_post_event_observation(self, observation: PostEventObservation) -> None:
        observation.validate()
        if observation.decision_id not in {r.decision_id for r in self.decisions}:
            raise ValueError("post-event observation references unknown decision")
        self.post_event_observations.append(observation)

    def observations_for(self, decision_id: str) -> tuple[PostEventObservation, ...]:
        return tuple(
            item for item in self.post_event_observations
            if item.decision_id == decision_id
        )


def extract_prior_components(components: Mapping[str, float]) -> dict[str, float]:
    """Extract score terms that came from learned/legend prior influence."""

    prefixes=(
        "learned_",
        "learned:",
        "learned_comping:",
        "legend:",
    )
    return {
        key:value
        for key,value in components.items()
        if key.startswith(prefixes)
    }


def append_ranked_decision(
    log: DecisionContextLog | None,
    *,
    player_id: str,
    decision_kind: str,
    ensemble_state: EnsembleState | None,
    candidates: Sequence[CandidateAudit],
    selected_candidate_id: str,
    selected_score: float,
    contextual_gate_weights: Mapping[str, float] | None = None,
    reasons: Sequence[str] = (),
    provenance: Sequence[str] = (),
) -> DecisionRecord | None:
    """Append one generic player decision without importing player internals.

    Player modules adapt their own candidate/score types into CandidateAudit.
    Shared Core stores only instrument-neutral audit data.
    """

    if log is None:
        return None
    context = (
        snapshot_ensemble_context(ensemble_state)
        if ensemble_state is not None
        else None
    )
    decision_id = (
        f"{player_id}:{decision_kind}:"
        f"{context.generation if context is not None else 'na'}:"
        f"{len(log.decisions)}"
    )
    candidate_tuple = tuple(candidates)
    selected = next(
        (candidate for candidate in candidate_tuple
         if candidate.candidate_id == selected_candidate_id),
        None,
    )
    if selected is None:
        raise ValueError("selected candidate audit entry is required")

    record = DecisionRecord(
        decision_id=decision_id,
        player_id=player_id,
        decision_kind=decision_kind,
        context=context,
        candidates=candidate_tuple,
        selected_candidate_id=selected_candidate_id,
        selected_score=selected_score,
        prior_contributions=extract_prior_components(selected.components),
        contextual_gate_weights=dict(contextual_gate_weights or {}),
        reasons=tuple(reasons),
        provenance=tuple(provenance),
    )
    log.append_decision(record)
    return record
