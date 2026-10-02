"""Interactive drum-solo trading and motif-response layer.

This module consumes a compact projection of another player's phrase.  The
projection is drummer-owned and intentionally does not redefine Shared Core
motif/ensemble semantics.  It represents only the rhythmic evidence needed by
the drum realization layer.

The response policy follows the project invariant:
listen -> infer response intention -> commit one immediate gesture -> listen.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .model import DrumGesture, DrumHit, DrummerRuntimeContext, DrumVoice, GestureRole, Limb
from .solo import DrumSoloPlan, DrumSoloState, SoloCandidate, SoloDevelopment


class TradeLength(str, Enum):
    FOUR = "four_bars"
    EIGHT = "eight_bars"


class ResponseRelation(str, Enum):
    ECHO = "echo"
    RHYTHMIC_VARIATION = "rhythmic_variation"
    ORCHESTRAL_ANSWER = "orchestral_answer"
    DENSITY_CONTRAST = "density_contrast"
    SPACE_ANSWER = "space_answer"
    CONTINUE_DIRECTION = "continue_direction"
    RESOLVE = "resolve"


@dataclass(frozen=True)
class EnsembleMotifProjection:
    """Rhythmic/expressive projection of the phrase just heard.

    onset_positions are normalized inside the source phrase to 0..1.  This
    object is an adapter; Shared Core remains owner of canonical motif memory.
    """
    onset_positions: tuple[float, ...]
    accent_positions: tuple[float, ...] = ()
    density: float = 0.5
    energy_direction: float = 0.0
    syncopation: float = 0.5
    terminal_space: float = 0.0
    source_role: str = "soloist"

    def validate(self) -> None:
        for pos in self.onset_positions + self.accent_positions:
            if not 0.0 <= pos <= 1.0:
                raise ValueError("motif positions must be normalized to 0..1")
        for name in ("density", "syncopation", "terminal_space"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if not -1.0 <= self.energy_direction <= 1.0:
            raise ValueError("energy_direction must be within -1..1")


@dataclass(frozen=True)
class TradingPlan:
    length: TradeLength = TradeLength.FOUR
    relation: ResponseRelation = ResponseRelation.RHYTHMIC_VARIATION
    bars_into_drum_turn: int = 0
    answer_strength: float = 0.65
    preserve_recognizability: float = 0.65

    def validate(self) -> None:
        if self.bars_into_drum_turn < 0:
            raise ValueError("bars_into_drum_turn may not be negative")
        for name in ("answer_strength", "preserve_recognizability"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")

    @property
    def total_bars(self) -> int:
        return 4 if self.length is TradeLength.FOUR else 8

    @property
    def turn_position(self) -> float:
        return min(1.0, self.bars_into_drum_turn / max(1, self.total_bars - 1))


@dataclass(frozen=True)
class TradeCandidate:
    gesture: DrumGesture
    relation: ResponseRelation
    score: float
    reasons: tuple[tuple[str, float], ...] = ()


def motif_similarity(
    source: EnsembleMotifProjection,
    response_positions: tuple[float, ...],
    tolerance: float = 0.09,
) -> float:
    """Simple onset-set recall measure for response recognizability."""
    source.validate()
    if not source.onset_positions or not response_positions:
        return 0.0
    matches = sum(
        1
        for s in source.onset_positions
        if any(abs(s - r) <= tolerance for r in response_positions)
    )
    return matches / len(source.onset_positions)


def _relation_voice(relation: ResponseRelation, index: int) -> DrumVoice:
    if relation is ResponseRelation.ORCHESTRAL_ANSWER:
        return (DrumVoice.HIGH_TOM, DrumVoice.MID_TOM, DrumVoice.FLOOR_TOM)[index % 3]
    if relation is ResponseRelation.DENSITY_CONTRAST:
        return DrumVoice.BASS_DRUM if index % 2 else DrumVoice.SNARE
    if relation is ResponseRelation.RESOLVE:
        return DrumVoice.CRASH
    return DrumVoice.SNARE


def _limb(voice: DrumVoice, index: int) -> Limb:
    if voice is DrumVoice.BASS_DRUM:
        return Limb.RIGHT_FOOT
    if voice is DrumVoice.CRASH:
        return Limb.RIGHT_HAND
    return Limb.LEFT_HAND if index % 2 else Limb.RIGHT_HAND


def _current_motif_match(source: EnsembleMotifProjection, context: DrummerRuntimeContext) -> bool:
    if not source.onset_positions:
        return False
    phase = context.position_in_bar_beats / context.beats_per_bar
    return any(abs(phase - x) <= 0.09 for x in source.onset_positions)


def build_trade_candidates(
    trade: TradingPlan,
    source: EnsembleMotifProjection,
    solo_plan: DrumSoloPlan,
    context: DrummerRuntimeContext,
    state: DrumSoloState,
) -> tuple[TradeCandidate, ...]:
    trade.validate()
    source.validate()
    solo_plan.validate()
    context.validate()

    relations = (
        ResponseRelation.ECHO,
        ResponseRelation.RHYTHMIC_VARIATION,
        ResponseRelation.ORCHESTRAL_ANSWER,
        ResponseRelation.DENSITY_CONTRAST,
        ResponseRelation.SPACE_ANSWER,
        ResponseRelation.CONTINUE_DIRECTION,
        ResponseRelation.RESOLVE,
    )
    candidates: list[TradeCandidate] = []
    motif_here = _current_motif_match(source, context)

    for relation in relations:
        if relation is ResponseRelation.SPACE_ANSWER:
            gesture = DrumGesture(
                role=GestureRole.SPACE,
                tags=frozenset({"trade", trade.length.value, relation.value}),
                provenance=("drum_player", "trades_engine"),
            )
        else:
            voice = _relation_voice(relation, state.gestures_committed)
            velocity = int(50 + 55 * solo_plan.intensity)
            if relation is ResponseRelation.CONTINUE_DIRECTION:
                velocity += int(14 * source.energy_direction)
            gesture = DrumGesture(
                hits=(DrumHit(
                    voice=voice,
                    limb=_limb(voice, state.gestures_committed),
                    velocity=max(1, min(127, velocity)),
                    articulation=relation.value,
                ),),
                role=GestureRole.FILL if relation is not ResponseRelation.RESOLVE else GestureRole.ACCENT,
                tags=frozenset({"trade", trade.length.value, relation.value}),
                provenance=("drum_player", "trades_engine"),
            )
            gesture.validate()

        score = 0.0
        reasons: list[tuple[str, float]] = []

        if relation is ResponseRelation.ECHO:
            v = (0.52 if motif_here else 0.12) * trade.preserve_recognizability
            score += v
            reasons.append(("motif_recognition", v))

        if relation is ResponseRelation.RHYTHMIC_VARIATION:
            v = 0.30 + 0.30 * trade.answer_strength
            if motif_here:
                v += 0.14
            score += v
            reasons.append(("recognizable_variation", v))

        if relation is ResponseRelation.ORCHESTRAL_ANSWER:
            v = 0.28 + 0.20 * trade.answer_strength
            score += v
            reasons.append(("change_color_keep_dialogue", v))

        if relation is ResponseRelation.DENSITY_CONTRAST:
            v = 0.22 + 0.30 * abs(source.density - solo_plan.density)
            if source.density > 0.72:
                v += 0.18
            score += v
            reasons.append(("density_contrast", v))

        if relation is ResponseRelation.SPACE_ANSWER:
            v = 0.12 + 0.42 * source.terminal_space + 0.20 * context.ensemble_activity
            score += v
            reasons.append(("answer_with_space", v))

        if relation is ResponseRelation.CONTINUE_DIRECTION:
            v = 0.20 + 0.30 * abs(source.energy_direction)
            score += v
            reasons.append(("continue_energy_direction", v))

        nearing_end = trade.turn_position >= 0.75 or context.phrase_position >= 0.9
        if relation is ResponseRelation.RESOLVE:
            v = 0.10 + (0.62 if nearing_end else -0.18)
            if context.section_transition:
                v += 0.28
            score += v
            reasons.append(("trade_reentry", v))

        # Avoid literal parroting throughout a full trade.
        if relation is ResponseRelation.ECHO and state.motif_repetitions >= 1:
            score -= 0.22
            reasons.append(("avoid_parroting", -0.22))

        candidates.append(TradeCandidate(gesture, relation, score, tuple(reasons)))

    return tuple(candidates)


def perform_one_trade_gesture(
    trade: TradingPlan,
    source: EnsembleMotifProjection,
    solo_plan: DrumSoloPlan,
    context: DrummerRuntimeContext,
    state: DrumSoloState,
) -> TradeCandidate:
    """Choose one response gesture. Caller listens again after this event."""
    candidates = build_trade_candidates(trade, source, solo_plan, context, state)
    chosen = max(candidates, key=lambda c: c.score)
    # Map interaction relation onto solo-development memory without inventing
    # Shared Core motif state.
    development = {
        ResponseRelation.ECHO: SoloDevelopment.REPEAT,
        ResponseRelation.RHYTHMIC_VARIATION: SoloDevelopment.DISPLACE,
        ResponseRelation.ORCHESTRAL_ANSWER: SoloDevelopment.ORCHESTRATE,
        ResponseRelation.DENSITY_CONTRAST: SoloDevelopment.CONTRAST,
        ResponseRelation.SPACE_ANSWER: SoloDevelopment.ADD_SPACE,
        ResponseRelation.CONTINUE_DIRECTION: SoloDevelopment.STATE,
        ResponseRelation.RESOLVE: SoloDevelopment.RESOLVE,
    }[chosen.relation]
    state.observe(chosen.gesture, development)
    return chosen
