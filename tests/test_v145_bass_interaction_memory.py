from music_intelligence.bass.interaction_grammar import (
    BassInteractionContext,
    BassInteractionIntent,
    choose_bass_interaction_intent,
)
from music_intelligence.bass.performance_memory import (
    BassArticulation,
    BassCommittedAction,
    BassPerformanceMemory,
)
from music_intelligence.reasoning.ensemble_state import InteractionKind
from music_intelligence.reasoning.interaction_scheduler import InteractionDirective
from music_intelligence.reasoning.legend_style_core import CandidateEvent


def event(pitch, tags=()):
    return CandidateEvent(
        pitch_midi=pitch,
        duration_beats=1.0,
        tags=frozenset(tags),
        source_family="test",
    )


def test_memory_tracks_stepwise_momentum_and_direction():
    memory = BassPerformanceMemory()
    for p in (40, 42, 44, 45):
        memory.commit(BassCommittedAction(event(p)))
    snap = memory.snapshot()
    assert snap.recent_pitches[-4:] == (40, 42, 44, 45)
    assert snap.consecutive_step_count == 3
    assert snap.consecutive_direction_count == 3
    assert snap.phrase_register_slope > 0


def test_phrase_ending_is_opportunity_not_automatic_fill():
    decision = choose_bass_interaction_intent(
        BassInteractionContext(soloist_phrase_ending=True)
    )
    assert decision.response_opportunity > 0
    assert decision.intent is not BassInteractionIntent.FILL


def test_other_fill_makes_bass_yield_response_space():
    directive = InteractionDirective(
        player_id="bass",
        interaction=InteractionKind.ANSWER,
        confidence=.8,
    )
    decision = choose_bass_interaction_intent(
        BassInteractionContext(
            directive=directive,
            soloist_phrase_ending=True,
            drum_fill_active=True,
        )
    )
    assert decision.intent is BassInteractionIntent.YIELD
    assert decision.complexity_delta < 0


def test_recent_complexity_creates_hold_obligation():
    memory = BassPerformanceMemory()
    for i, p in enumerate((40, 47, 42, 49, 43, 50)):
        memory.commit(BassCommittedAction(
            event(p),
            articulation=BassArticulation.GHOSTED if i % 2 else BassArticulation.ACCENTED,
            interaction_role="fill",
        ))
    decision = choose_bass_interaction_intent(
        BassInteractionContext(
            memory=memory.snapshot(),
            soloist_phrase_ending=True,
        )
    )
    assert decision.intent is BassInteractionIntent.HOLD
    assert decision.complexity_delta < 0


def test_form_boundary_forces_reset_intention():
    decision = choose_bass_interaction_intent(
        BassInteractionContext(form_boundary=True)
    )
    assert decision.intent is BassInteractionIntent.RESET
    assert decision.register_recovery >= .45
