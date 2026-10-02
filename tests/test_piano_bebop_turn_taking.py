from music_intelligence.reasoning.legend_style_core import CandidateEvent
from players.piano import (
    BebopTurnTakingEvidence,
    BebopTurnTakingType,
    PianoSoloContext,
    PianoSoloEvaluator,
    classify_bebop_turn_taking,
)


def test_supported_handoff_reentry_classifier():
    evidence = classify_bebop_turn_taking(
        foreground_during_pre=0.18,
        low_support_during_pre=0.81,
        attack_support_during_pre=0.38,
        foreground_post_during=4.87,
    )
    assert evidence.episode_type is BebopTurnTakingType.SUPPORTED_HANDOFF_REENTRY


def test_collective_release_reentry_classifier():
    evidence = classify_bebop_turn_taking(
        foreground_during_pre=0.19,
        low_support_during_pre=0.38,
        attack_support_during_pre=0.24,
        foreground_post_during=5.41,
    )
    assert evidence.episode_type is BebopTurnTakingType.COLLECTIVE_RELEASE_REENTRY


def test_foreground_continues_classifier():
    evidence = classify_bebop_turn_taking(
        foreground_during_pre=2.06,
        low_support_during_pre=0.73,
        attack_support_during_pre=1.79,
        foreground_post_during=0.86,
    )
    assert evidence.episode_type is BebopTurnTakingType.FOREGROUND_CONTINUES


def test_supported_reentry_prefers_continuation_over_duplicate_entry():
    evaluator=PianoSoloEvaluator()
    turn=BebopTurnTakingEvidence(
        BebopTurnTakingType.SUPPORTED_HANDOFF_REENTRY,
        0.18,
        0.81,
        0.38,
        4.87,
        1.0,
        0.0,
    )
    ctx=PianoSoloContext(turn_taking=turn)
    continuation=CandidateEvent(
        69,
        0.5,
        tags=frozenset({"continuation","connector","directed_target"}),
    )
    duplicate=CandidateEvent(
        69,
        0.5,
        tags=frozenset({"phrase_entry"}),
    )
    a=evaluator.evaluate(continuation,ctx)
    b=evaluator.evaluate(duplicate,ctx)
    assert a.components.get("turn_reentry_continuation",0)>0
    assert b.components.get("turn_duplicate_entry",0)<0


def test_continuing_foreground_can_reward_contrast_space():
    evaluator=PianoSoloEvaluator()
    ctx=PianoSoloContext(
        turn_taking=BebopTurnTakingEvidence(
            BebopTurnTakingType.FOREGROUND_CONTINUES,
            2.0,
            0.7,
            1.4,
            0.9,
            1.0,
            0.0,
        )
    )
    rest=CandidateEvent(None,0.5,tags=frozenset({"rest"}))
    dense=CandidateEvent(72,0.25,tags=frozenset({"dense_run"}))
    a=evaluator.evaluate(rest,ctx)
    b=evaluator.evaluate(dense,ctx)
    assert a.components.get("foreground_continues_contrast",0)>0
    assert b.components.get("foreground_continues_overdensity",0)<0


def test_turn_taking_evidence_has_no_actor_claim_by_default():
    evidence=classify_bebop_turn_taking(
        foreground_during_pre=0.2,
        low_support_during_pre=0.9,
        attack_support_during_pre=0.8,
        foreground_post_during=3.0,
    )
    assert evidence.actor_attribution_confidence == 0.0
    assert not hasattr(evidence,"future_phrase")
    assert not hasattr(evidence,"next_notes")
