from music_intelligence.learning.canonical_position import (
    canonicalize_structural_positions,
    position_feature_map,
)
from music_intelligence.learning.form_position import FormMap, FormSection
from music_intelligence.learning.representation import (
    StructuralPerformanceData,
    StructuralPerformanceEvent,
)


def event(event_id,onset):
    return StructuralPerformanceEvent(
        event_id=event_id,
        onset_beats=onset,
        duration_beats=.5,
        pitch_midi=60,
    )


def test_meter_projects_global_beats_into_measure_and_beat():
    data=StructuralPerformanceData(
        source_id="x",
        events=(event("a",5.5),),
        meter="4/4",
    )
    out=canonicalize_structural_positions(data)
    p=out.events[0].metric_form_position
    assert p.measure_index == 1
    assert p.display_measure == 2
    assert p.beat_in_measure == 1.5
    assert p.display_beat == 2.5
    assert p.section_id is None


def test_form_map_projects_section_and_iteration():
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
        events=(event("a",34*4+2.0),),
        meter="4/4",
        form_map=fmap,
    )
    out=canonicalize_structural_positions(data)
    p=out.events[0].metric_form_position
    assert p.form_iteration == 1
    assert p.measure_index == 2
    assert p.section_id == "A1"
    assert p.section_measure_index == 2
    assert p.beat_in_measure == 2.0


def test_position_features_keep_human_and_internal_coordinates():
    data=StructuralPerformanceData(
        source_id="x",
        events=(event("a",4.0),),
        meter="4/4",
    )
    e=canonicalize_structural_positions(data).events[0]
    f=position_feature_map(e)
    assert f["measure_index"] == 1
    assert f["measure_number"] == 2
    assert f["beat_in_measure"] == 0.0
    assert f["beat_number"] == 1.0
