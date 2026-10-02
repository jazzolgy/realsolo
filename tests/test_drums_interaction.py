import pytest

from music_intelligence.drums.interaction import (
    EnsembleMotifProjection,
    ResponseRelation,
    TradeLength,
    TradingPlan,
    build_trade_candidates,
    motif_similarity,
    perform_one_trade_gesture,
)
from music_intelligence.drums.model import (
    DrummerRuntimeContext,
    DrumVoice,
    Limb,
)
from music_intelligence.drums.physical import (
    four_limb_solo_gesture,
    limb_can_play,
    validate_kit_reachability,
)
from music_intelligence.drums.solo import DrumSoloPlan, DrumSoloState, SoloArc


def test_motif_similarity_rewards_recognizable_onset_shape():
    source = EnsembleMotifProjection((0.0, 0.5, 0.75))
    assert motif_similarity(source, (0.02, 0.52, 0.76)) > 0.9
    assert motif_similarity(source, (0.2, 0.35)) < 0.5


def test_trade_response_uses_source_phrase_not_context_free_solo():
    source = EnsembleMotifProjection(
        (0.0, 0.5, 0.75),
        density=0.55,
        energy_direction=0.4,
    )
    trade = TradingPlan(length=TradeLength.FOUR, bars_into_drum_turn=0)
    plan = DrumSoloPlan(arc=SoloArc.DEVELOP, adventurousness=0.45)
    state = DrumSoloState(statements=1)
    ctx = DrummerRuntimeContext(position_in_bar_beats=2.0)

    candidates = build_trade_candidates(trade, source, plan, ctx, state)
    assert {c.relation for c in candidates} >= {
        ResponseRelation.RHYTHMIC_VARIATION,
        ResponseRelation.ORCHESTRAL_ANSWER,
        ResponseRelation.SPACE_ANSWER,
    }


def test_trade_resolves_near_end_instead_of_overplaying():
    source = EnsembleMotifProjection((0.0, 0.5), terminal_space=0.2)
    trade = TradingPlan(length=TradeLength.FOUR, bars_into_drum_turn=3)
    plan = DrumSoloPlan(arc=SoloArc.REENTRY, target_reentry=True)
    state = DrumSoloState(statements=5)
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=3.0,
        phrase_position=0.95,
        section_transition=True,
    )

    chosen = perform_one_trade_gesture(trade, source, plan, ctx, state)
    assert chosen.relation is ResponseRelation.RESOLVE


def test_four_limb_gesture_uses_each_limb_at_most_once_and_is_reachable():
    gesture = four_limb_solo_gesture(
        right_hand=DrumVoice.RIDE,
        left_hand=DrumVoice.SNARE,
        right_foot=True,
        left_foot_hihat=True,
    )
    validate_kit_reachability(gesture)
    assert {h.limb for h in gesture.hits} == {
        Limb.RIGHT_HAND, Limb.LEFT_HAND, Limb.RIGHT_FOOT, Limb.LEFT_FOOT
    }


def test_default_physical_model_rejects_foot_on_snare():
    assert not limb_can_play(Limb.RIGHT_FOOT, DrumVoice.SNARE)
