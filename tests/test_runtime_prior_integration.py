import pytest

from music_intelligence.learning import LearningDomain, LearningPriorView
from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    PlayerPresence,
    PlayerRole,
    TransportState,
)
from music_intelligence.reasoning.groove_context import GrooveFeel, build_groove_context
from music_intelligence.reasoning.interaction_scheduler import schedule_player
from music_intelligence.reasoning.legend_style_core import CandidateEvent, MusicalContextVector
from players.piano.comping import (
    CompingActionType,
    InteractionRole,
    PianoCompingCandidate,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
)
from players.piano.solo import PianoSoloContext, PianoSoloEvaluator


def _prior(domain, *, numeric=None, numeric_weights=None, categorical=None, categorical_weights=None):
    return LearningPriorView(
        domain=domain,
        numeric_features=numeric or {},
        categorical_counts=categorical or {},
        feedback_bias={},
        observations=1,
        numeric_weights=numeric_weights or {},
        categorical_weights=categorical_weights or {},
        weighted_observations=1.0,
    )


def test_solo_candidate_scoring_consumes_solo_phrase_prior_softly():
    prior = _prior(
        LearningDomain.SOLO_PHRASE,
        numeric={"entry_phase": 0.0},
        numeric_weights={"entry_phase": 1.0},
    )
    candidate = CandidateEvent(60, .5, 0.0, frozenset({"chord_tone"}))
    context = PianoSoloContext(musical=MusicalContextVector(metric_position=0.0))

    plain = PianoSoloEvaluator().evaluate(candidate, context)
    learned = PianoSoloEvaluator(solo_phrase_prior=prior).evaluate(candidate, context)

    assert learned.total > plain.total
    assert learned.components["learned_solo_entry_phase"] > 0


def test_comping_candidate_scoring_consumes_weighted_density_prior():
    prior = _prior(
        LearningDomain.COMPING,
        numeric={"density": 0.0},
        numeric_weights={"density": 1.0},
    )
    candidate = PianoCompingCandidate(
        action_type=CompingActionType.SILENCE,
        role=InteractionRole.LAY_OUT,
        duration_beats=1.0,
    )
    context = PianoCompingContext()
    musical = MusicalContextVector()
    state = PianoCompingState()

    plain = PianoCompingEvaluator().evaluate(candidate, context, musical, state)
    learned = PianoCompingEvaluator(comping_prior=prior).evaluate(
        candidate, context, musical, state
    )

    assert learned.total > plain.total
    assert learned.components["learned_comping_density"] > 0


def test_interaction_scheduler_uses_response_role_prior_as_confidence_nudge_only():
    prior = _prior(
        LearningDomain.ENSEMBLE_INTERACTION,
        categorical={"response_role": {"drums": 1}},
        categorical_weights={"response_role": {"drums": 1.0}},
    )
    state = EnsembleState(
        transport=TransportState(beat=0.0, bar=1),
        players=(PlayerPresence("drums", "drum_set", PlayerRole.DRUMS),),
    )

    plain = schedule_player(state, "drums")
    learned = schedule_player(state, "drums", interaction_prior=prior)

    assert learned.interaction == plain.interaction
    assert learned.confidence > plain.confidence
    assert "learned_interaction_prior" in learned.tags


def test_groove_context_can_fill_missing_grammar_from_weighted_prior():
    prior = _prior(
        LearningDomain.RHYTHM_GROOVE,
        categorical={"best_groove_grammar": {"swing": 1, "bossa": 1}},
        categorical_weights={"best_groove_grammar": {"swing": 1.5, "bossa": .5}},
    )

    groove = build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=140.0,
        grammar_id="",
        confidence=.7,
        groove_prior=prior,
    )

    assert groove.grammar_id == "swing"
    assert groove.confidence > .7
    assert "weighted_groove_prior" in groove.provenance
