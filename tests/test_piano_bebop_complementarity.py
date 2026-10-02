from music_intelligence.reasoning.legend_style_core import CandidateEvent
from players.piano import (
    BebopPhraseSpaceEvidence,
    CompingActionType,
    EnsembleBreathType,
    EnsembleComplementarityEvidence,
    InteractionRole,
    PhraseSpaceType,
    PianoCompingCandidate,
    PianoSoloContext,
    PianoSoloEvaluator,
    classify_ensemble_complementarity,
    evaluate_bebop_breath_comping_bias,
)


def test_complementarity_classifier_finds_foreground_handoff():
    evidence = classify_ensemble_complementarity(
        foreground_ratio=0.12,
        low_harmonic_support_ratio=0.9,
        percussive_support_ratio=1.0,
        post_foreground_ratio=2.5,
    )
    assert evidence.breath_type is EnsembleBreathType.FOREGROUND_HANDOFF


def test_complementarity_classifier_finds_collective_release():
    evidence = classify_ensemble_complementarity(
        foreground_ratio=0.15,
        low_harmonic_support_ratio=0.3,
        percussive_support_ratio=0.4,
        post_foreground_ratio=2.0,
    )
    assert evidence.breath_type is EnsembleBreathType.COLLECTIVE_RELEASE


def test_foreground_handoff_can_reward_space_and_pickup():
    evaluator = PianoSoloEvaluator()
    evidence = EnsembleComplementarityEvidence(
        breath_type=EnsembleBreathType.FOREGROUND_HANDOFF,
        foreground_drop=0.85,
        low_harmonic_support=0.85,
        percussive_support=0.95,
        post_foreground_reentry=0.6,
        confidence=1.0,
    )
    ctx = PianoSoloContext(ensemble_complementarity=evidence)
    rest = CandidateEvent(None, 0.5, tags=frozenset({"rest"}))
    pickup = CandidateEvent(
        70,
        0.5,
        onset_offset_beats=-0.125,
        tags=frozenset({"pickup", "anticipation", "syncopated_entry"}),
    )
    rest_score = evaluator.evaluate(rest, ctx)
    pickup_score = evaluator.evaluate(pickup, ctx)
    assert rest_score.components.get("foreground_handoff_space", 0) > 0
    assert pickup_score.components.get("foreground_handoff_pickup", 0) > 0


def test_foreground_handoff_penalizes_dense_run():
    evaluator = PianoSoloEvaluator()
    ctx = PianoSoloContext(
        ensemble_complementarity=EnsembleComplementarityEvidence(
            breath_type=EnsembleBreathType.FOREGROUND_HANDOFF,
            foreground_drop=0.8,
            low_harmonic_support=0.9,
            percussive_support=0.9,
            confidence=1.0,
        )
    )
    dense = CandidateEvent(72, 0.25, tags=frozenset({"dense_run"}))
    score = evaluator.evaluate(dense, ctx)
    assert score.components.get("foreground_handoff_overfill", 0) < 0


def test_collective_release_can_frame_directed_reentry():
    evaluator = PianoSoloEvaluator()
    ctx = PianoSoloContext(
        ensemble_complementarity=EnsembleComplementarityEvidence(
            breath_type=EnsembleBreathType.COLLECTIVE_RELEASE,
            foreground_drop=0.85,
            low_harmonic_support=0.25,
            percussive_support=0.3,
            post_foreground_reentry=0.8,
            confidence=1.0,
        )
    )
    entry = CandidateEvent(
        69,
        0.5,
        tags=frozenset({"phrase_entry", "directed_target", "resolution_path"}),
    )
    score = evaluator.evaluate(entry, ctx)
    assert score.components.get("collective_release_reentry", 0) > 0


def test_comping_handoff_prefers_space_over_sustained_overfill():
    evidence = EnsembleComplementarityEvidence(
        breath_type=EnsembleBreathType.FOREGROUND_HANDOFF,
        foreground_drop=0.85,
        low_harmonic_support=0.9,
        percussive_support=0.9,
        confidence=1.0,
    )
    silence = PianoCompingCandidate(
        action_type=CompingActionType.SILENCE,
        role=InteractionRole.LAY_OUT,
        duration_beats=0.5,
    )
    sustained = PianoCompingCandidate(
        action_type=CompingActionType.SUSTAINED_SUPPORT,
        role=InteractionRole.SUPPORT,
        duration_beats=1.0,
    )
    a = evaluate_bebop_breath_comping_bias(silence, evidence)
    b = evaluate_bebop_breath_comping_bias(sustained, evidence)
    assert a.total > 0
    assert b.total < 0


def test_complementarity_keeps_actor_attribution_unknown_by_default():
    evidence = classify_ensemble_complementarity(
        foreground_ratio=0.2,
        low_harmonic_support_ratio=0.8,
        percussive_support_ratio=0.9,
        post_foreground_ratio=2.2,
    )
    assert evidence.actor_attribution_confidence == 0.0


def test_harmonic_carried_handoff_is_recognized():
    from players.piano import SupportCarryMode, support_carry_mode
    evidence = EnsembleComplementarityEvidence(
        breath_type=EnsembleBreathType.FOREGROUND_HANDOFF,
        foreground_drop=0.8,
        low_harmonic_support=0.95,
        percussive_support=0.4,
        confidence=1.0,
    )
    assert support_carry_mode(evidence) is SupportCarryMode.HARMONIC_CARRIED


def test_percussive_carried_handoff_can_reward_thin_harmonic_anchor():
    evaluator = PianoSoloEvaluator()
    ctx = PianoSoloContext(
        ensemble_complementarity=EnsembleComplementarityEvidence(
            breath_type=EnsembleBreathType.FOREGROUND_HANDOFF,
            foreground_drop=0.8,
            low_harmonic_support=0.3,
            percussive_support=0.95,
            confidence=1.0,
        )
    )
    anchor = CandidateEvent(
        67,
        0.5,
        tags=frozenset({"guide_tone", "harmonic_identity"}),
    )
    score = evaluator.evaluate(anchor, ctx)
    assert score.components.get("percussive_carried_harmonic_support", 0) > 0


def test_mixed_support_can_reward_preserving_space():
    evaluator = PianoSoloEvaluator()
    ctx = PianoSoloContext(
        ensemble_complementarity=EnsembleComplementarityEvidence(
            breath_type=EnsembleBreathType.FOREGROUND_HANDOFF,
            foreground_drop=0.8,
            low_harmonic_support=0.95,
            percussive_support=0.95,
            confidence=1.0,
        )
    )
    rest = CandidateEvent(None, 0.5, tags=frozenset({"rest"}))
    score = evaluator.evaluate(rest, ctx)
    assert score.components.get("mixed_support_preserve_space", 0) > 0
