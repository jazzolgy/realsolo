from music_intelligence.reasoning.motif import (
    MotifEvaluationContext,
    MotifFeedback,
    MotifGenerationContext,
    MotifLearningState,
    MotifMemory,
    MotifMemoryState,
    choose_motif_policy,
    generate_motif_candidates,
    transform_motif,
    update_motif_learning,
)
from music_intelligence.reasoning.solo_grammar import SoloDevelopmentOperation


def test_generator_produces_identity_not_exact_future_notes():
    candidates=generate_motif_candidates(MotifGenerationContext())
    assert candidates
    x=candidates[0]
    assert not hasattr(x.identity,"future_notes")
    assert not hasattr(x.identity,"pitch_sequence")
    assert 1 <= x.identity.event_count_hint <= 8


def test_generator_can_mix_vocabulary_and_ensemble_sources():
    candidates=generate_motif_candidates(MotifGenerationContext(
        vocabulary_seed_id="PARKER-SIG-017",
        ensemble_seed_id="drum-gesture-4",
        rhythmic_seed=(.5,.5,1.0),
        interval_seed=(2,1,-3),
        interaction_role="ANSWER",
    ))
    assert any(x.source_type.value=="hybrid" for x in candidates)


def test_memory_promotes_then_dormant_then_reactivates():
    memory=MotifMemory()
    identity=generate_motif_candidates(MotifGenerationContext())[0].identity
    memory.observe(identity,development_success=.8)
    entry=memory.observe(identity,development_success=.8)
    assert entry.state is MotifMemoryState.THEMATIC
    for _ in range(8):
        memory.advance(dormant_after_ticks=8)
    assert memory.entries[identity.motif_id].state is MotifMemoryState.DORMANT
    recalled=memory.recall(identity.motif_id)
    assert recalled is not None and recalled.state is MotifMemoryState.ACTIVE


def test_feedback_changes_learned_source_and_operation_bias():
    state=MotifLearningState()
    feedback=MotifFeedback(
        source_type=generate_motif_candidates(MotifGenerationContext())[0].source_type,
        operation=SoloDevelopmentOperation.VARY,
        musical_fit=.9,
        memorability=.9,
        development_success=.95,
        ensemble_fit=.8,
        novelty=.7,
        coherence=.9,
    )
    learned=update_motif_learning(state,feedback)
    assert learned.observations==1
    assert learned.operation_bias(SoloDevelopmentOperation.VARY)>0


def test_transformations_preserve_relative_identity_only():
    identity=generate_motif_candidates(MotifGenerationContext(interval_seed=(2,1,-3)))[0].identity
    inverted=transform_motif(identity,SoloDevelopmentOperation.INVERT)
    assert inverted.interval_schema==tuple(-x for x in identity.interval_schema)


def test_policy_returns_development_operation():
    decision=choose_motif_policy(
        MotifGenerationContext(),
        MotifEvaluationContext(),
    )
    assert isinstance(decision.development_operation,SoloDevelopmentOperation)
    assert decision.evaluation.transformability>0
