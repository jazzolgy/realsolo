from music_intelligence.learning.engine import LearningPriorView, SharedLearningEngine
from music_intelligence.learning.representation import LearningDomain, LearningArtifact
from music_intelligence.reasoning.hierarchical_priors import HierarchicalPriorSet
from music_intelligence.reasoning.runtime_prior_bundle import (
    hierarchical_priors_from_learning_engine,
)
from music_intelligence.reasoning.runtime_legend_selector import (
    legend_choice_for,
    select_runtime_legends,
)
from realtime.ensemble_app.stage1_quartet import Stage1QuartetRuntime


def _tick(runtime, beat=0.0):
    return runtime.decide(
        "Cm7","F7",
        beat_in_bar=beat,
        bar_index=0,
        total_bars=32,
        tempo_bpm=172.0,
        section="A",
    )


def test_generic_bebop_selects_small_parker_sax_prior_but_not_empty_bill_evans():
    choices=select_runtime_legends(style_tags=("jazz","bebop","swing"))
    sax=legend_choice_for(choices,"sax")
    assert sax is not None
    assert sax.legend_id=="charlie_parker"
    assert 0.0 < sax.weight < .5
    assert legend_choice_for(choices,"piano") is None


def test_lafaro_requires_explicit_or_matching_interactive_trio_context():
    generic=select_runtime_legends(style_tags=("jazz","bebop","swing"))
    assert legend_choice_for(generic,"bass") is None

    interactive=select_runtime_legends(
        style_tags=("jazz","modern_jazz_trio","interactive_trio")
    )
    bass=legend_choice_for(interactive,"bass")
    assert bass is not None
    assert bass.legend_id=="scott_lafaro"


def test_empty_bill_evans_profile_is_not_activated_even_by_override():
    choices=select_runtime_legends(
        style_tags=("jazz","swing"),
        overrides={"piano":"bill_evans"},
    )
    assert legend_choice_for(choices,"piano") is None


def test_autumn_leaves_sax_receives_contextual_parker_prior():
    quartet=Stage1QuartetRuntime.create(172.0)
    result=_tick(quartet)
    sax=next(
        g for g in result.gestures
        if g.source=="player/sax:canonical_immediate"
    )
    assert sax.annotations["legend_id"]=="charlie_parker"


def test_promoted_runtime_prior_can_reach_sax_policy_projection():
    prior=LearningPriorView(
        domain=LearningDomain.GENRE,
        numeric_features={"policy.continuity":.95},
        categorical_counts={},
        feedback_bias={},
        observations=8,
        numeric_weights={"policy.continuity":8.0},
        categorical_weights={},
        weighted_observations=8.0,
    )
    quartet=Stage1QuartetRuntime.create(172.0)
    quartet.hierarchical_priors=HierarchicalPriorSet(genre_prior=prior)
    result=_tick(quartet)
    sax=next(
        g for g in result.gestures
        if g.source=="player/sax:canonical_immediate"
    )
    assert float(sax.annotations["policy_projection_confidence"]) > 0.0


def test_explicit_lafaro_override_reaches_bass_runtime_context():
    quartet=Stage1QuartetRuntime.create(172.0)
    quartet.legend_overrides={"bass":"scott_lafaro"}
    result=_tick(quartet)
    bass=next(d for d in result.decisions if d.player_id=="bass")
    assert "player/bass:sequential_runner" in bass.intent.provenance



def test_evidence_only_learning_does_not_enter_audible_runtime_prior():
    engine=SharedLearningEngine()
    artifact=LearningArtifact(
        artifact_id="evidence-only",
        source_id="research-source",
        domain=LearningDomain.GENRE,
        feature_schema="policy.v1",
        features={"policy.continuity":.92},
        confidence=.9,
        provenance=("research_evidence_only",),
    )
    engine.ingest_artifacts((artifact,),learn=False,study_as_evidence=True)
    assert engine.evidence_prior(LearningDomain.GENRE).observations==1
    assert hierarchical_priors_from_learning_engine(engine) is None


def test_promoted_learning_enters_audible_runtime_prior():
    engine=SharedLearningEngine()
    artifact=LearningArtifact(
        artifact_id="promoted",
        source_id="authorized-source",
        domain=LearningDomain.GENRE,
        feature_schema="policy.v1",
        features={"policy.continuity":.92},
        confidence=.9,
        provenance=("training_authorized",),
    )
    engine.ingest_artifacts((artifact,),learn=True,study_as_evidence=True)
    priors=hierarchical_priors_from_learning_engine(engine)
    assert priors is not None
    assert priors.genre_prior is not None
    assert priors.genre_prior.numeric_features["policy.continuity"]==.92
