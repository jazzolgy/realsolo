from music_intelligence.learning import (
    MusicalScoreCoordinate,
    musical_score_coordinate_from_metric_form,
)
from music_intelligence.learning.form_position import MetricFormPosition
from music_intelligence.learning.canonical_position import (
    canonical_score_coordinate_for_event,
)
from music_intelligence.learning.representation import (
    StructuralPerformanceData,
    StructuralPerformanceEvent,
)
from music_intelligence.corpus import (
    song_from_normalized_record,
    coordinate_from_realchord,
)


def test_metric_form_position_is_intermediate_not_persisted_identity():
    metric=MetricFormPosition(
        measure_index=4,
        beat_in_measure=2.5,
        meter_numerator=4,
        meter_denominator=4,
        form_id="AABA32",
        section_id="A1",
        section_measure_index=4,
        form_iteration=2,
        confidence=.9,
    )
    coord=musical_score_coordinate_from_metric_form(
        metric,
        song_id="test_tune",
        score_source_id="manual_form:test",
    )
    assert isinstance(coord,MusicalScoreCoordinate)
    assert coord.bar==5
    assert coord.beat==2.5
    assert coord.chorus_index==2
    assert coord.section=="A1"


def test_listener_event_adapts_to_shared_canonical_coordinate():
    event=StructuralPerformanceEvent(
        event_id="e1",
        onset_beats=6.0,
        duration_beats=.5,
        pitch_midi=67,
        harmony_label="Dm7",
        phrase_id="p1",
    )
    data=StructuralPerformanceData(
        source_id="src",
        events=(event,),
        meter="4/4",
    )
    coord=canonical_score_coordinate_for_event(
        event,data,song_id="Tune"
    )
    assert isinstance(coord,MusicalScoreCoordinate)
    assert coord.bar==2
    assert coord.beat==2.0
    assert coord.chord_label=="Dm7"


def test_realchord_adapter_returns_same_canonical_coordinate_type():
    song=song_from_normalized_record({
        "realchord_id":"rc.test",
        "title":"Tune",
        "measures":[{
            "measure":1,
            "section":"A",
            "chords":[{"beat":1.0,"symbol":"Cm7"}],
        }],
    })
    coord=coordinate_from_realchord(song,measure=1,beat=1.0)
    assert isinstance(coord,MusicalScoreCoordinate)
    assert coord.realchord_id=="rc.test"
