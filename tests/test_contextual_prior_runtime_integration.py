import pytest

from music_intelligence.learning import LearningDomain, LearningPriorView
from music_intelligence.reasoning.contextual_prior_gating import (
    head_gating_context,
    improvisation_gating_context,
)
from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    InteractionEvent,
    InteractionKind,
    PlayerPresence,
    PlayerRole,
    TransportState,
)
from music_intelligence.reasoning.groove_context import GrooveFeel, build_groove_context
from music_intelligence.reasoning.hierarchical_priors import (
    HierarchicalPriorSet,
    PriorLayerWeights,
)
from music_intelligence.reasoning.interaction_scheduler import schedule_player
from music_intelligence.reasoning.legend_style_core import (
    CandidateEvent,
    MusicalContextVector,
)
from music_intelligence.reasoning.phrase_space import PhraseSpaceEvidence
from music_intelligence.reasoning.ensemble_complementarity import EnsembleComplementarityEvidence
from music_intelligence.reasoning.turn_taking import TurnTakingEvidence
from music_intelligence.reasoning.harmonic_turn import HarmonicTurnContext
from music_intelligence.reasoning.head_fidelity import HeadFidelityMode
from players.piano.head_interpretation import (
    HeadInterpretationContext,
    gated_head_prior_hierarchy,
)
from players.piano.solo import PianoSoloContext, PianoSoloEvaluator


def _prior(domain, *, numeric=None, categorical=None):
    numeric=numeric or {}
    categorical=categorical or {}
    return LearningPriorView(
        domain=domain,
        numeric_features=numeric,
        categorical_counts=categorical,
        feedback_bias={},
        observations=1,
        numeric_weights={k:1.0 for k in numeric},
        categorical_weights={
            k:{label:1.0 for label in values}
            for k,values in categorical.items()
        },
        weighted_observations=1.0,
    )


def test_head_gating_keeps_priors_below_improvisation_weights():
    hierarchy=HierarchicalPriorSet(
        domain_prior=_prior(LearningDomain.SOLO_PHRASE,numeric={"entry_phase":0.0}),
        weights=PriorLayerWeights(),
    )
    head=gated_head_prior_hierarchy(
        hierarchy,
        HeadInterpretationContext(
            fidelity_mode=HeadFidelityMode.STRICT,
            ensemble_density=.0,
            strong_beat=True,
        ),
    )
    assert head is not None
    assert head.weights.domain < hierarchy.weights.domain
    assert head.weights.style < hierarchy.weights.style
    assert head.weights.legend < hierarchy.weights.legend


def test_dense_high_confidence_solo_context_attenuates_learned_entry_bias():
    prior=_prior(LearningDomain.SOLO_PHRASE,numeric={"entry_phase":0.0})
    hierarchy=HierarchicalPriorSet(domain_prior=prior)

    candidate=CandidateEvent(
        pitch_midi=60,
        duration_beats=.5,
        onset_offset_beats=0.0,
        tags=frozenset({"chord_tone"}),
    )

    quiet=PianoSoloContext(
        musical=MusicalContextVector(metric_position=0.0),
        ensemble_density=0.0,
        left_hand_comping_activity=0.0,
        phrase_space=PhraseSpaceEvidence(confidence=0.0),
        ensemble_complementarity=EnsembleComplementarityEvidence(confidence=0.0),
        turn_taking=TurnTakingEvidence(confidence=0.0),
        harmonic_turn=HarmonicTurnContext(),
    )
    dense=PianoSoloContext(
        musical=MusicalContextVector(metric_position=0.0,tension=1.0,phrase_maturity=1.0),
        ensemble_density=1.0,
        left_hand_comping_activity=1.0,
        phrase_space=PhraseSpaceEvidence(confidence=1.0),
        ensemble_complementarity=EnsembleComplementarityEvidence(confidence=1.0),
        turn_taking=TurnTakingEvidence(confidence=1.0),
        harmonic_turn=HarmonicTurnContext(confidence=1.0),
    )

    evaluator=PianoSoloEvaluator(prior_hierarchy=hierarchy)
    quiet_score=evaluator.evaluate(candidate,quiet)
    dense_score=evaluator.evaluate(candidate,dense)

    assert quiet_score.components["learned_solo_entry_phase"] > dense_score.components["learned_solo_entry_phase"]


def test_interaction_prior_is_weaker_when_live_interaction_evidence_is_strong():
    prior=_prior(
        LearningDomain.ENSEMBLE_INTERACTION,
        categorical={"response_role":{"drums":1}},
    )
    base_state=EnsembleState(
        transport=TransportState(beat=0.0,bar=1),
        players=(PlayerPresence("drums","drum_set",PlayerRole.DRUMS),),
    )
    strong_state=EnsembleState(
        transport=TransportState(beat=0.0,bar=1),
        players=(PlayerPresence("drums","drum_set",PlayerRole.DRUMS),),
        recent_interactions=(
            InteractionEvent("drums",InteractionKind.SUPPORT,confidence=1.0),
        ),
        ensemble_density=1.0,
    )

    base=schedule_player(base_state,"drums",interaction_prior=prior)
    strong=schedule_player(strong_state,"drums",interaction_prior=prior)

    assert "learned_interaction_prior" in base.tags
    assert "learned_interaction_prior" in strong.tags
    assert strong.confidence - .58 < base.confidence - .58


def test_explicit_groove_grammar_remains_authoritative_under_prior_gating():
    prior=_prior(
        LearningDomain.RHYTHM_GROOVE,
        categorical={"best_groove_grammar":{"swing":1}},
    )
    groove=build_groove_context(
        GrooveFeel.BOSSA,
        tempo_bpm=120.0,
        grammar_id="bossa",
        confidence=.7,
        groove_prior=prior,
        prior_gating_context=improvisation_gating_context(
            ensemble_complexity=1.0,
            live_context_confidence=1.0,
        ),
    )
    assert groove.grammar_id=="bossa"
    assert any(x.startswith("contextual_prior_gate:") for x in groove.provenance)
