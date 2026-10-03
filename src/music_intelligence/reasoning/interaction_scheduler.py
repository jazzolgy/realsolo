"""v1.44 ensemble interaction scheduler.

The scheduler coordinates *roles and tendencies* for the next immediate action.
It is not a centralized composer and never chooses pitches, voicings, bass
lines, or drum patterns.

Each player receives an InteractionDirective derived from the shared
EnsembleState. The player may use that directive as one input to its own
candidate evaluation, then commits one immediate action and publishes a new
PlayerActionIntent.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from music_intelligence.learning.engine import LearningPriorView
from .learning_prior_runtime import categorical_prior_bias

from .ensemble_state import (
    EnsembleState,
    InteractionKind,
    PlayerActionIntent,
    PlayerPresence,
    PlayerRole,
    player_view,
)


@dataclass(frozen=True)
class InteractionDirective:
    player_id: str
    interaction: InteractionKind
    target_player_ids: tuple[str, ...] = ()
    density_delta: float = 0.0
    energy_delta: float = 0.0
    leadership_delta: float = 0.0
    space_priority: float = 0.0
    confidence: float = 0.5
    reasons: tuple[str, ...] = ()
    tags: frozenset[str] = frozenset()

    def validate(self) -> None:
        if not self.player_id:
            raise ValueError("player_id is required")
        for value, name in (
            (self.density_delta, "density_delta"),
            (self.energy_delta, "energy_delta"),
            (self.leadership_delta, "leadership_delta"),
        ):
            if not -1.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within -1..1")
        if not 0.0 <= self.space_priority <= 1.0:
            raise ValueError("space_priority must be within 0..1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")


def _latest_intents(state: EnsembleState) -> dict[str, PlayerActionIntent]:
    out: dict[str, PlayerActionIntent] = {}
    for intent in state.intents:
        out[intent.player_id] = intent
    return out


def _presence(state: EnsembleState, player_id: str) -> PlayerPresence:
    for p in state.players:
        if p.player_id == player_id:
            return p
    raise ValueError(f"unknown player_id: {player_id}")


def _default_for_role(role: PlayerRole) -> InteractionKind:
    if role in {PlayerRole.SOLOIST, PlayerRole.LEADER, PlayerRole.MELODY}:
        return InteractionKind.LEAD
    if role is PlayerRole.BASS:
        return InteractionKind.LOCK
    if role in {PlayerRole.DRUMS, PlayerRole.COMPER, PlayerRole.SUPPORT}:
        return InteractionKind.SUPPORT
    if role is PlayerRole.FOLLOWER:
        return InteractionKind.FOLLOW
    return InteractionKind.SUPPORT


def _ending_leader(
    state: EnsembleState,
    *,
    exclude_player_id: str,
) -> PlayerActionIntent | None:
    candidates = [
        i for i in _latest_intents(state).values()
        if i.player_id != exclude_player_id
        and i.leadership >= .55
        and i.phrase_maturity >= .72
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda x: (x.phrase_maturity, x.leadership))


def _strong_other_leader(
    state: EnsembleState,
    *,
    exclude_player_id: str,
) -> PlayerActionIntent | None:
    candidates = [
        i for i in _latest_intents(state).values()
        if i.player_id != exclude_player_id and i.leadership >= .65
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda x: x.leadership)


def schedule_player(
    state: EnsembleState,
    player_id: str,
    *,
    interaction_prior: LearningPriorView | None = None,
) -> InteractionDirective:
    """Return a coordination directive for one player's next immediate action."""
    state.validate()
    p = _presence(state, player_id)
    view = player_view(state, player_id)
    own = state.intent_for(player_id)
    leader = _strong_other_leader(state, exclude_player_id=player_id)
    ending = _ending_leader(state, exclude_player_id=player_id)

    interaction = _default_for_role(p.role)
    density_delta = 0.0
    energy_delta = 0.0
    leadership_delta = 0.0
    space_priority = 0.0
    confidence = .58
    reasons: list[str] = []
    tags: set[str] = set()
    targets: tuple[str, ...] = ()

    # Phrase handoff is more specific than general "someone else is leading".
    if ending is not None:
        targets = (ending.player_id,)
        tags.add("phrase_handoff_window")
        if p.role is PlayerRole.DRUMS:
            interaction = InteractionKind.SETUP
            energy_delta += .10
            density_delta += .04
            confidence = .84
            reasons.append("leader phrase is nearing an ending; prepare setup")
        elif p.role is PlayerRole.BASS:
            interaction = InteractionKind.LOCK
            density_delta -= .04
            confidence = .78
            reasons.append("leader phrase is nearing an ending; preserve harmonic/rhythmic floor")
        elif p.role in {PlayerRole.COMPER, PlayerRole.SUPPORT}:
            interaction = InteractionKind.ANSWER
            density_delta -= .02
            leadership_delta += .08
            confidence = .76
            reasons.append("leader phrase ending opens a response window")
        elif p.role in {PlayerRole.SOLOIST, PlayerRole.MELODY, PlayerRole.LEADER}:
            interaction = InteractionKind.ANSWER
            leadership_delta += .12
            confidence = .78
            reasons.append("another leader phrase is ending; answer rather than overlap")

    elif leader is not None:
        targets = (leader.player_id,)
        tags.add("other_player_leading")
        if p.role is PlayerRole.BASS:
            interaction = InteractionKind.LOCK
            density_delta -= .03
            confidence = .80
            reasons.append("support active leader with stable bass continuity")
        elif p.role is PlayerRole.DRUMS:
            interaction = InteractionKind.SUPPORT
            confidence = .78
            reasons.append("support active leader without competing for foreground")
        else:
            interaction = InteractionKind.YIELD
            density_delta -= .16
            leadership_delta -= .18
            space_priority = max(space_priority, .70)
            confidence = .82
            reasons.append("another player has strong leadership; yield foreground")

    # Ensemble crowding is a global constraint. Bass/drums should not simply
    # disappear, so their density reduction is smaller than melody/comping.
    if state.ensemble_density >= .72:
        tags.add("ensemble_crowded")
        if p.role in {PlayerRole.BASS, PlayerRole.DRUMS}:
            density_delta -= .06
        else:
            density_delta -= .14
            space_priority = max(space_priority, .65)
        reasons.append("high ensemble density calls for reduced competing activity")
        confidence = max(confidence, .74)

    if state.space_available <= .25:
        tags.add("low_space")
        if interaction not in {InteractionKind.LOCK, InteractionKind.SETUP}:
            interaction = InteractionKind.HOLD_SPACE
        density_delta -= .08
        space_priority = max(space_priority, .80)
        reasons.append("little ensemble space is currently available")
        confidence = max(confidence, .76)

    # If no one is clearly leading and the current player is a designated
    # soloist/melody voice, encourage leadership instead of deadlock.
    if state.leader_player_id is None and p.role in {
        PlayerRole.SOLOIST,
        PlayerRole.MELODY,
        PlayerRole.LEADER,
    }:
        if ending is None:
            interaction = InteractionKind.LEAD
            leadership_delta += .12
            confidence = max(confidence, .72)
            reasons.append("no current leader; designated foreground player may lead")

    # Near a form boundary, drums can signal and rhythm section can stabilize.
    near_boundary = state.transport.form_position >= .96
    if near_boundary:
        tags.add("form_boundary")
        if p.role is PlayerRole.DRUMS:
            interaction = InteractionKind.TRANSITION
            energy_delta += .08
            confidence = max(confidence, .82)
            reasons.append("form boundary invites a transition cue")
        elif p.role is PlayerRole.BASS:
            interaction = InteractionKind.LOCK
            confidence = max(confidence, .76)
            reasons.append("form boundary benefits from stable bass orientation")

    # Continuity: if a player has just committed a strong intent and no more
    # specific ensemble event overrides it, avoid gratuitous role flipping.
    if own is not None and not reasons:
        interaction = own.interaction
        confidence = .64
        reasons.append("maintain current interaction unless new ensemble evidence redirects it")

    if interaction in {
        InteractionKind.ANSWER,
        InteractionKind.FOLLOW,
        InteractionKind.SUPPORT,
        InteractionKind.SETUP,
    }:
        learned_response_role = categorical_prior_bias(
            interaction_prior,
            "response_role",
            p.role.value,
            max_bonus=.08,
        )
        if learned_response_role.active:
            confidence = min(
                1.0,
                confidence + learned_response_role.confidence_delta,
            )
            reasons.append(learned_response_role.reason)
            tags.add("learned_interaction_prior")

    directive = InteractionDirective(
        player_id=player_id,
        interaction=interaction,
        target_player_ids=targets,
        density_delta=max(-1.0, min(1.0, density_delta)),
        energy_delta=max(-1.0, min(1.0, energy_delta)),
        leadership_delta=max(-1.0, min(1.0, leadership_delta)),
        space_priority=space_priority,
        confidence=confidence,
        reasons=tuple(reasons),
        tags=frozenset(tags),
    )
    directive.validate()
    return directive


def schedule_ensemble(
    state: EnsembleState,
    *,
    interaction_prior: LearningPriorView | None = None,
) -> tuple[InteractionDirective, ...]:
    """Compute simultaneous coordination advice from one immutable snapshot.

    All directives are derived from the same state generation. They should be
    applied by players as guidance; after commitments, the state is updated and
    the scheduler runs again.
    """
    state.validate()
    return tuple(
        schedule_player(
            state,
            p.player_id,
            interaction_prior=interaction_prior,
        )
        for p in state.active_players()
    )


def directive_to_intent(
    directive: InteractionDirective,
    *,
    previous: PlayerActionIntent | None = None,
) -> PlayerActionIntent:
    """Project a directive into a provisional intent baseline.

    A player may further modify this after its instrument-specific candidate
    choice. No exact musical event is created here.
    """
    directive.validate()
    base_density = previous.density if previous else .5
    base_energy = previous.energy if previous else .5
    base_tension = previous.tension if previous else .5
    base_leadership = previous.leadership if previous else .0
    phrase_maturity = previous.phrase_maturity if previous else .0

    return PlayerActionIntent(
        player_id=directive.player_id,
        interaction=directive.interaction,
        density=max(0.0, min(1.0, base_density + directive.density_delta)),
        energy=max(0.0, min(1.0, base_energy + directive.energy_delta)),
        tension=base_tension,
        space_request=directive.space_priority,
        leadership=max(0.0, min(1.0, base_leadership + directive.leadership_delta)),
        phrase_maturity=phrase_maturity,
        target_player_ids=directive.target_player_ids,
        tags=directive.tags,
        provenance=("interaction_scheduler_v144",),
    )
