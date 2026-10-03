from realtime.ensemble_app.listener_shared_core_adapter import coordinate_from_listener_estimate
from music_intelligence.learning.score_alignment import MusicalScoreCoordinate


def test_listener_metric_estimate_becomes_canonical_coordinate():
    coord=coordinate_from_listener_estimate(
        {
            "measure_index":7,
            "beat_in_measure":2.5,
            "form_length_bars":32,
            "chorus_index":2,
            "section":"A2",
        },
        song_id="Autumn Leaves",
        confidence=.72,
    )
    assert isinstance(coord,MusicalScoreCoordinate)
    assert coord.bar==8
    assert coord.form_bar==8
    assert coord.chorus_index==2
    assert coord.provenance[-1]=="canonical_coordinate_adapter"


def test_listener_does_not_persist_position_when_detector_has_no_musical_address():
    assert coordinate_from_listener_estimate(
        {"confidence":.8},
        song_id="Unknown",
    ) is None
