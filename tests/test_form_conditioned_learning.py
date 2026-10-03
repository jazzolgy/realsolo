from music_intelligence.learning.engine import SharedLearningEngine
from music_intelligence.learning.extractors import extract_learning_artifacts
from music_intelligence.learning.form_position import FormMap, FormSection, MeterSegment
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


def test_unresolved_metric_artifact_is_stored_but_does_not_change_prior():
    data=StructuralPerformanceData(
        source_id="unresolved",
        events=(e(0,0),e(1,1),e(2,2)),
        meter="",
    )
    artifacts=extract_learning_artifacts(data)
    engine=SharedLearningEngine()
    added=engine.ingest_artifacts(artifacts,learn=False,study_as_evidence=True)
    assert added == len(artifacts)
    prior=engine.evidence_prior(LearningDomain.COMPING)
    assert prior.observations == 0
    assert prior.unresolved_metric_observations >= 1


def test_same_pattern_at_different_form_positions_has_distinct_artifact_identity():
    fmap=FormMap(
        form_id="song",
        meter_numerator=4,
        meter_denominator=4,
        sections=(
            FormSection("verse",0,4),
            FormSection("chorus",4,4),
        ),
    )
    verse=StructuralPerformanceData(
        source_id="same",
        events=(e(0,0),e(1,1),e(2,2)),
        meter="4/4",
        form_map=fmap,
    )
    chorus=StructuralPerformanceData(
        source_id="same",
        events=(e(0,16),e(1,17),e(2,18)),
        meter="4/4",
        form_map=fmap,
    )
    a1=[a for a in extract_learning_artifacts(verse) if a.domain is LearningDomain.COMPING][0]
    a2=[a for a in extract_learning_artifacts(chorus) if a.domain is LearningDomain.COMPING][0]
    assert a1.artifact_id != a2.artifact_id
    assert a1.features["metric_form_context"]["sections"] != a2.features["metric_form_context"]["sections"]


def test_hierarchical_form_path_supports_classical_or_nested_pop_forms():
    fmap=FormMap(
        form_id="sonata_mvt1",
        meter_numerator=4,
        meter_denominator=4,
        sections=(
            FormSection("exposition",0,32,section_type="large_section"),
            FormSection("primary_theme",0,8,parent_section_id="exposition",section_type="theme"),
            FormSection("transition",8,8,parent_section_id="exposition",section_type="transition"),
        ),
    )
    p=fmap.position_from_absolute_beat(2.0)
    assert p.section_id == "primary_theme"
    assert p.form_path == ("exposition","primary_theme")


def test_form_map_supports_meter_changes():
    fmap=FormMap(
        form_id="mixed_meter",
        meter_numerator=4,
        meter_denominator=4,
        sections=(FormSection("A",0,8),),
        meter_segments=(MeterSegment(2,3,4),),
    )
    # m1 4 qn + m2 4 qn + m3 3 qn; 8 qn is the first beat of measure 3.
    p=fmap.position_from_absolute_beat(8.0)
    assert p.measure_index == 2
    assert p.beat_in_measure == 0.0
    assert p.meter_numerator == 3
    assert p.meter_denominator == 4
