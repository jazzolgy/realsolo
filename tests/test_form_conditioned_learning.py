from music_intelligence.learning.engine import SharedLearningEngine
from music_intelligence.learning.extractors import extract_learning_artifacts
from music_intelligence.learning.form_position import FormMap, FormSection
from music_intelligence.learning.representation import (
    LearningDomain,
    StructuralPerformanceData,
    StructuralPerformanceEvent,
)


def e(i,onset,role="comping"):
    return StructuralPerformanceEvent(
        event_id=f"e{i}",
        onset_beats=onset,
        duration_beats=.5,
        pitch_midi=60+i,
        role=role,
        confidence=.9,
    )


def test_every_learning_artifact_receives_metric_form_context():
    fmap=FormMap(
        form_id="AABA32",
        meter_numerator=4,
        meter_denominator=4,
        cycle_measures=32,
        sections=(
            FormSection("A1",0,8),
            FormSection("A2",8,8),
            FormSection("B",16,8),
            FormSection("A3",24,8),
        ),
    )
    data=StructuralPerformanceData(
        source_id="x",
        events=(e(0,0),e(1,1),e(2,4),e(3,5)),
        meter="4/4",
        form_map=fmap,
    )
    artifacts=extract_learning_artifacts(data)
    assert artifacts
    for artifact in artifacts:
        ctx=artifact.features["metric_form_context"]
        assert ctx["resolved_metric"] is True
        assert ctx["form_id"] == "AABA32"


def test_engine_builds_form_conditioned_prior():
    fmap=FormMap(
        form_id="song",
        meter_numerator=4,
        meter_denominator=4,
        sections=(FormSection("verse",0,4),),
    )
    data=StructuralPerformanceData(
        source_id="x",
        events=(e(0,0),e(1,1),e(2,2)),
        meter="4/4",
        form_map=fmap,
    )
    artifacts=extract_learning_artifacts(data)
    engine=SharedLearningEngine()
    engine.ingest_artifacts(artifacts,learn=False,study_as_evidence=True)
    prior=engine.evidence_prior(LearningDomain.COMPING)
    assert prior.form_context_observations
    key=next(iter(prior.form_context_observations))
    assert "form=song" in key
    assert "section=verse" in key


def test_six_eight_projection_uses_eighth_note_meter_units():
    data=StructuralPerformanceData(
        source_id="x",
        events=(e(0,1.5),),
        meter="6/8",
    )
    from music_intelligence.learning.canonical_position import canonicalize_structural_positions
    p=canonicalize_structural_positions(data).events[0].metric_form_position
    assert p.measure_index == 0
    assert p.beat_in_measure == 3.0
    assert p.display_beat == 4.0
