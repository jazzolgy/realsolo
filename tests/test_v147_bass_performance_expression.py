from music_intelligence.bass import (
    BassContext,
    BassInteractionContext,
    BassInteractionDecision,
    BassInteractionIntent,
    BassMode,
    BassPerformanceMemory,
    BassCommittedAction,
    BassArticulation,
    choose_bass_interaction_intent,
    generate_immediate_bass_candidates,
    realize_bass_expression,
)
from music_intelligence.bass.performance_grammar import (
    ArticulationIntent,
    BassGrammarDecision,
    GrooveRelation,
    MetricRole,
    MotionStrategy,
    TargetStrategy,
)
from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from music_intelligence.reasoning.legend_style_core import CandidateEvent


def ev(source, root, symbol, pcs):
    return HarmonicEvidence(
        source=source,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
    )


def grammar(metric=MetricRole.HARMONIC_ANCHOR, articulation=ArticulationIntent.NEUTRAL):
    return BassGrammarDecision(
        metric_role=metric,
        motion_strategy=MotionStrategy.CHORDAL,
        target_strategy=TargetStrategy.CURRENT_ROOT,
        groove_relation=GrooveRelation.ON_PULSE,
        articulation_intent=articulation,
        score_delta=0.0,
    )


def test_expression_separates_notated_and_sounding_duration():
    p = realize_bass_expression(
        mode="walking",
        grammar=grammar(),
    )
    assert 0.0 < p.sounding_length_ratio < 1.1


def test_anchor_and_yield_have_different_attack_profiles():
    anchor = realize_bass_expression(
        mode="walking",
        grammar=grammar(),
        interaction=BassInteractionDecision(intent=BassInteractionIntent.ANCHOR),
    )
    yield_ = realize_bass_expression(
        mode="walking",
        grammar=grammar(),
        interaction=BassInteractionDecision(intent=BassInteractionIntent.YIELD),
    )
    assert anchor.accent > yield_.accent
    assert anchor.sounding_length_ratio > yield_.sounding_length_ratio


def test_build_adds_forward_energy_without_large_fixed_offset():
    p = realize_bass_expression(
        mode="walking",
        grammar=grammar(),
        interaction=BassInteractionDecision(intent=BassInteractionIntent.BUILD),
    )
    assert p.accent > 0.52
    assert -12.0 <= p.microtiming_ms <= 12.0


def test_recent_ghosts_reduce_new_ghost_opportunity():
    memory = BassPerformanceMemory()
    memory.commit(BassCommittedAction(
        CandidateEvent(pitch_midi=40, duration_beats=1.0, source_family="test"),
        articulation=BassArticulation.GHOSTED,
        interaction_role="fill",
    ))
    sparse = realize_bass_expression(
        mode="walking",
        grammar=grammar(metric=MetricRole.PREPARATION),
        interaction=BassInteractionDecision(
            intent=BassInteractionIntent.FILL,
            response_opportunity=.8,
        ),
    )
    restrained = realize_bass_expression(
        mode="walking",
        grammar=grammar(metric=MetricRole.PREPARATION),
        memory=memory.snapshot(),
        interaction=BassInteractionDecision(
            intent=BassInteractionIntent.FILL,
            response_opportunity=.8,
        ),
    )
    assert restrained.ghost_opportunity < sparse.ghost_opportunity


def test_immediate_candidate_carries_expression_profile():
    frame = HarmonicFrame(
        expected=ev(HarmonySource.EXPECTED, 0, "Cm7", {0, 3, 7, 10}),
    )
    items = generate_immediate_bass_candidates(
        frame,
        BassContext(mode=BassMode.WALKING, beat_in_measure=0.0),
    )
    assert items
    assert all(0.0 <= x.expression.accent <= 1.0 for x in items)
    assert all(0.0 < x.expression.sounding_length_ratio <= 1.1 for x in items)
