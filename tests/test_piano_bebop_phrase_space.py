from music_intelligence.reasoning.legend_style_core import CandidateEvent
from players.piano import (
    BebopPhraseSpaceEvidence,
    PhraseSpaceType,
    PianoSoloContext,
    PianoSoloEvaluator,
    classify_phrase_space,
)


def test_classifier_distinguishes_quiet_active_and_deep_release():
    quiet = classify_phrase_space(
        energy_ratio_to_context=0.55,
        attack_ratio_to_context=0.95,
        reentry_ratio=1.4,
    )
    deep = classify_phrase_space(
        energy_ratio_to_context=0.25,
        attack_ratio_to_context=0.5,
        reentry_ratio=1.7,
    )
    assert quiet.space_type is PhraseSpaceType.QUIET_ACTIVE
    assert deep.space_type is PhraseSpaceType.DEEP_RELEASE


def test_quiet_active_space_can_reward_rest_and_penalize_dense_run():
    evaluator = PianoSoloEvaluator()
    ctx = PianoSoloContext(
        phrase_space=BebopPhraseSpaceEvidence(
            space_type=PhraseSpaceType.QUIET_ACTIVE,
            energy_drop=0.5,
            attack_persistence=0.9,
            confidence=1.0,
        )
    )
    rest = CandidateEvent(None, 0.5, tags=frozenset({"rest"}))
    dense = CandidateEvent(72, 0.25, tags=frozenset({"dense_run"}))
    a = evaluator.evaluate(rest, ctx)
    b = evaluator.evaluate(dense, ctx)
    assert a.components.get("quiet_active_space", 0) > 0
    assert b.components.get("quiet_active_density", 0) < 0


def test_deep_release_can_support_directed_reentry():
    evaluator = PianoSoloEvaluator()
    ctx = PianoSoloContext(
        phrase_space=BebopPhraseSpaceEvidence(
            space_type=PhraseSpaceType.DEEP_RELEASE,
            energy_drop=0.75,
            attack_persistence=0.4,
            reentry_contrast=0.7,
            confidence=1.0,
        )
    )
    candidate = CandidateEvent(
        70,
        0.5,
        onset_offset_beats=-0.125,
        tags=frozenset({
            "phrase_entry",
            "anticipation",
            "directed_target",
            "resolution_path",
        }),
    )
    score = evaluator.evaluate(candidate, ctx)
    assert score.components.get("deep_release_reentry", 0) > 0
    assert score.components.get("reentry_direction", 0) > 0


def test_deep_release_does_not_force_immediate_fill():
    evaluator = PianoSoloEvaluator()
    ctx = PianoSoloContext(
        phrase_space=BebopPhraseSpaceEvidence(
            space_type=PhraseSpaceType.DEEP_RELEASE,
            energy_drop=0.8,
            attack_persistence=0.3,
            reentry_contrast=0.1,
            confidence=1.0,
        )
    )
    rest = CandidateEvent(None, 0.5, tags=frozenset({"rest"}))
    score = evaluator.evaluate(rest, ctx)
    assert score.components.get("deep_release_hold_space", 0) > 0


def test_phrase_space_evidence_claims_no_actor_by_default():
    evidence = classify_phrase_space(
        energy_ratio_to_context=0.3,
        attack_ratio_to_context=0.5,
        reentry_ratio=1.5,
    )
    assert evidence.actor_attribution_confidence == 0.0
