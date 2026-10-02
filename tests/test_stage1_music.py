from realtime.ensemble_app.stage1_music import (
    Stage1Soloist,
    accompaniment_frame,
    parse_chord,
)


def test_parse_common_jazz_chords():
    assert parse_chord("Dm7").pitch_classes == (2, 5, 9, 0)
    assert parse_chord("G7").pitch_classes == (7, 11, 2, 5)
    assert parse_chord("Cmaj7").pitch_classes == (0, 4, 7, 11)


def test_accompaniment_is_immediate_frame_not_future_sequence():
    frame = accompaniment_frame("Dm7", 1)
    assert len(frame["bass"]) == 1
    assert len(frame["comp"]) <= 4
    assert "drums" in frame


def test_soloist_commits_one_event_per_call():
    solo = Stage1Soloist()
    one = solo.choose("Dm7", "G7", beat_in_bar=0.0, phrase_step=0)
    two = solo.choose("Dm7", "G7", beat_in_bar=0.5, phrase_step=1)
    assert one["pitch"] is not None
    assert one["committed_count"] == 1
    assert two["committed_count"] == 2
