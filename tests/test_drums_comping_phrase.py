from music_intelligence.drums.bebop import (
    BebopCompIntent,
    BebopInteractionState,
)
from music_intelligence.drums.comping_phrase import (
    CompPhraseAction,
    SnareMotifIdentity,
    SnarePhraseMemory,
    build_snare_phrase_candidates,
    displaced_motif_match,
    motif_match_at_phase,
    update_snare_phrase_memory,
)
from music_intelligence.drums.model import DrummerRuntimeContext, DrummerSoftPlan


def test_first_snare_statement_can_create_local_motif():
    plan = DrummerSoftPlan()
    ctx = DrummerRuntimeContext(position_in_bar_beats=1.0)
    candidates = build_snare_phrase_candidates(
        plan,
        ctx,
        BebopInteractionState.SUPPORT,
        BebopCompIntent.ANSWER,
        SnarePhraseMemory(),
    )
    assert any(c.action is CompPhraseAction.STATE for c in candidates)


def test_exact_and_displaced_motif_are_distinct_relations():
    motif = SnareMotifIdentity((0.25,))
    assert motif_match_at_phase(motif, 0.25) > 0.9
    assert displaced_motif_match(motif, 0.375) > 0.9
    assert motif_match_at_phase(motif, 0.375) == 0.0


def test_immediate_repetition_is_penalized_relative_to_return_after_space():
    motif = SnareMotifIdentity((0.25,))
    plan = DrummerSoftPlan()
    ctx = DrummerRuntimeContext(position_in_bar_beats=1.0)

    immediate = build_snare_phrase_candidates(
        plan,
        ctx,
        BebopInteractionState.SUPPORT,
        BebopCompIntent.SUPPORT,
        SnarePhraseMemory(
            motif=motif,
            bars_since_motif_statement=0.25,
            consecutive_related_statements=1,
        ),
    )
    after_space = build_snare_phrase_candidates(
        plan,
        ctx,
        BebopInteractionState.SUPPORT,
        BebopCompIntent.SUPPORT,
        SnarePhraseMemory(
            motif=motif,
            bars_since_motif_statement=1.5,
            consecutive_related_statements=1,
            recent_space_bars=1.0,
        ),
    )

    immediate_repeat = next(c for c in immediate if c.action is CompPhraseAction.REPEAT)
    returned = next(c for c in after_space if c.action is CompPhraseAction.RETURN)
    assert returned.score_bias > immediate_repeat.score_bias


def test_coast_increases_phrase_level_space():
    plan = DrummerSoftPlan()
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.5)
    candidates = build_snare_phrase_candidates(
        plan,
        ctx,
        BebopInteractionState.COAST,
        BebopCompIntent.INTENTIONAL_NON_RESPONSE,
        SnarePhraseMemory(motif=SnareMotifIdentity((0.25,))),
    )
    space = next(c for c in candidates if c.action is CompPhraseAction.LEAVE_SPACE)
    assert space.score_bias > 0.5


def test_phrase_memory_never_contains_future_snare_sequence():
    memory = update_snare_phrase_memory(
        SnarePhraseMemory(),
        CompPhraseAction.STATE,
        phase=0.25,
    )
    assert memory.motif is not None
    assert memory.motif.onset_phases == (0.25,)
    assert not hasattr(memory, "future_hits")
    assert not hasattr(memory, "future_pattern")
