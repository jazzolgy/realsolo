from players.bass.interaction_grammar import (
    BassInteractionContext,
    BassInteractionIntent,
    choose_bass_interaction_intent,
)


def test_dense_ensemble_suppresses_bass_foreground_activity():
    decision=choose_bass_interaction_intent(
        BassInteractionContext(
            ensemble_activity=.90,
            soloist_phrase_ending=True,
        )
    )
    assert decision.intent in {
        BassInteractionIntent.HOLD,
        BassInteractionIntent.YIELD,
        BassInteractionIntent.ANCHOR,
    }
    assert decision.complexity_delta < 0


def test_open_ensemble_increases_response_opportunity():
    closed=choose_bass_interaction_intent(
        BassInteractionContext(ensemble_activity=.80)
    )
    open_=choose_bass_interaction_intent(
        BassInteractionContext(ensemble_activity=.20)
    )
    assert open_.response_opportunity > closed.response_opportunity
