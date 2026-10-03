"""Shared research/runtime representation for one musically meaningful moment.

A MusicalMoment aligns form, harmony, phrase/space, ensemble state, player
actions, and interaction relations on one timeline. It is descriptive context,
not a hidden decision engine and not a Player realization contract.

The representation intentionally keeps exact instrument realization out of the
shared schema. Player-specific pitch/voicing/string/limb details remain in
Player/Performance Evidence domains.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .ensemble_state import EnsembleState, InteractionKind


class MomentActionCommitment(str, Enum):
    OBSERVED = "observed"
    COMMITTED = "committed"
    PLAYED = "played"


@dataclass(frozen=True)
class MomentPosition:
    beat: float
    bar: int
    section: str = ""
    chorus: int = 0
    form_position: float = 0.0

    def validate(self) -> None:
        if self.bar < 0 or self.chorus < 0:
            raise ValueError("bar / chorus may not be negative")
        if not 0.0 <= self.form_position <= 1.0:
            raise ValueError("form_position must be within 0..1")


@dataclass(frozen=True)
class MomentHarmony:
    expected_ref: str | None = None
    observed_ref: str | None = None
    inferred_ref: str | None = None
    local_key_ref: str | None = None
    cadence_state: str = ""
    tension: float | None = None
    confidence: float = 0.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.tension is not None and not 0.0 <= self.tension <= 1.0:
            raise ValueError("harmony tension must be within 0..1 when known")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("harmony confidence must be within 0..1")


@dataclass(frozen=True)
class MomentPhraseState:
    phrase_id: str | None = None
    phrase_position: float | None = None
    maturity: float | None = None
    boundary_pressure: float | None = None
    space: float | None = None
    tension: float | None = None
    motif_id: str | None = None
    confidence: float = 0.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        for name in (
            "phrase_position",
            "maturity",
            "boundary_pressure",
            "space",
            "tension",
            "confidence",
        ):
            value=getattr(self,name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1 when known")


@dataclass(frozen=True)
class MomentGrooveState:
    grammar_id: str = ""
    feel: str = ""
    strength: float | None = None
    confidence: float = 0.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.strength is not None and not 0.0 <= self.strength <= 1.0:
            raise ValueError("groove strength must be within 0..1 when known")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("groove confidence must be within 0..1")


@dataclass(frozen=True)
class MomentPlayerAction:
    """Instrument-neutral description of one player's behavior in the moment."""

    player_id: str
    instrument: str
    role: str = ""
    action_type: str = ""
    interaction: str = ""
    commitment: MomentActionCommitment = MomentActionCommitment.OBSERVED
    density: float | None = None
    energy: float | None = None
    tension: float | None = None
    space: float | None = None
    register_center: float | None = None
    phrase_role: str = ""
    motif_id: str | None = None
    semantic_tags: frozenset[str] = frozenset()
    confidence: float = 0.0
    provenance: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.player_id:
            raise ValueError("player_id is required")
        if not self.instrument:
            raise ValueError("instrument is required")
        for name in ("density","energy","tension","space","confidence"):
            value=getattr(self,name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1 when known")
        if self.register_center is not None and not 0.0 <= self.register_center <= 1.0:
            raise ValueError("register_center must be normalized to 0..1")


@dataclass(frozen=True)
class MomentInteraction:
    source_player_id: str
    kind: str
    target_player_ids: tuple[str, ...] = ()
    confidence: float = 0.0
    tags: frozenset[str] = frozenset()
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.source_player_id:
            raise ValueError("interaction source_player_id is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("interaction confidence must be within 0..1")


@dataclass(frozen=True)
class MusicalMoment:
    """One aligned unit for study, runtime context, and offline comparison.

    MusicalMoment records what is happening together. It does not infer why an
    action happened, whether it was good, or how a Player must realize it.
    """

    moment_id: str
    position: MomentPosition
    harmony: MomentHarmony = field(default_factory=MomentHarmony)
    phrase: MomentPhraseState = field(default_factory=MomentPhraseState)
    groove: MomentGrooveState = field(default_factory=MomentGrooveState)
    player_actions: tuple[MomentPlayerAction, ...] = ()
    interactions: tuple[MomentInteraction, ...] = ()
    ensemble_density: float | None = None
    ensemble_energy: float | None = None
    ensemble_tension: float | None = None
    space_available: float | None = None
    leader_player_id: str | None = None
    confidence: float = 0.0
    provenance: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.moment_id:
            raise ValueError("moment_id is required")
        self.position.validate()
        self.harmony.validate()
        self.phrase.validate()
        self.groove.validate()
        for action in self.player_actions:
            action.validate()
        for interaction in self.interactions:
            interaction.validate()
        for name in (
            "ensemble_density",
            "ensemble_energy",
            "ensemble_tension",
            "space_available",
            "confidence",
        ):
            value=getattr(self,name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1 when known")

        player_ids={action.player_id for action in self.player_actions}
        if self.leader_player_id is not None and player_ids and self.leader_player_id not in player_ids:
            raise ValueError("leader_player_id must reference a player action when actions are present")


def musical_moment_from_ensemble_state(
    state: EnsembleState,
    *,
    moment_id: str,
    harmony: MomentHarmony | None = None,
    phrase: MomentPhraseState | None = None,
    player_actions: tuple[MomentPlayerAction, ...] = (),
    confidence: float = 0.0,
    provenance: tuple[str, ...] = ("shared_ensemble_state",),
    source_refs: tuple[str, ...] = (),
) -> MusicalMoment:
    """Snapshot Shared Ensemble State into a MusicalMoment.

    Existing Shared Core state is projected into the moment; no additional
    musical interpretation is invented here.
    """

    state.validate()
    groove=state.groove
    interactions=tuple(
        MomentInteraction(
            source_player_id=event.source_player_id,
            kind=event.kind.value if isinstance(event.kind, InteractionKind) else str(event.kind),
            target_player_ids=event.target_player_ids,
            confidence=event.confidence,
            tags=event.tags,
            provenance=("ensemble_state",),
        )
        for event in state.recent_interactions
    )
    moment=MusicalMoment(
        moment_id=moment_id,
        position=MomentPosition(
            beat=state.transport.beat,
            bar=state.transport.bar,
            section=state.transport.section,
            chorus=state.transport.chorus,
            form_position=state.transport.form_position,
        ),
        harmony=harmony or MomentHarmony(
            inferred_ref=state.harmonic_state_id,
            confidence=0.0,
            provenance=("ensemble_state:harmonic_state_ref",)
            if state.harmonic_state_id else (),
        ),
        phrase=phrase or MomentPhraseState(),
        groove=MomentGrooveState(
            grammar_id=groove.grammar_id if groove is not None else "",
            feel=groove.feel.value if groove is not None else "",
            strength=groove.groove_strength if groove is not None else 0.0,
            confidence=groove.confidence if groove is not None else 0.0,
            provenance=groove.provenance if groove is not None else (),
        ),
        player_actions=player_actions,
        interactions=interactions,
        ensemble_density=state.ensemble_density,
        ensemble_energy=state.ensemble_energy,
        ensemble_tension=state.ensemble_tension,
        space_available=state.space_available,
        leader_player_id=state.leader_player_id,
        confidence=confidence,
        provenance=provenance,
        source_refs=source_refs,
    )
    moment.validate()
    return moment
