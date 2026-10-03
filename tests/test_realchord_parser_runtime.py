from music_intelligence.corpus import (
    expand_playback_timeline,
    expected_harmony_for_state,
    future_harmony,
    parse_progression,
    session_state_at,
    song_from_normalized_record,
)


def test_parser_builds_normalized_expected_harmony_grid():
    measures, warnings = parse_progression("*A[T44C^7   |D-7 G7 Z")
    assert len(measures) == 2
    assert measures[0]["section"] == "A"
    assert measures[0]["time_signature"] == "4/4"
    assert measures[0]["chords"][0]["symbol"] == "C^7"
    assert measures[0]["chords"][0]["beat"] == 1.0
    assert [c["symbol"] for c in measures[1]["chords"]] == ["D-7", "G7"]


def test_normalized_adapter_accepts_canonical_expected_harmony_shape():
    song = song_from_normalized_record({
        "realchord_id": "rc_test",
        "title": "Test Tune",
        "composer": "Composer",
        "canonical": {
            "measures": [
                {
                    "measure": 1,
                    "section": "A",
                    "expected_harmony": [
                        {"beat": 1.0, "symbol": "C^7", "confidence": 0.95},
                        {"beat": 3.0, "symbol": "A7", "confidence": 0.95},
                    ],
                }
            ]
        },
    })
    assert [c.symbol for c in song.measure_at(1).chords] == ["C^7", "A7"]
    assert song.provenance == ()


def test_repeat_expansion_does_not_increment_chorus_index():
    song = song_from_normalized_record({
        "realchord_id": "rc_repeat",
        "title": "Repeat Tune",
        "measures": [
            {
                "measure": 1,
                "section": "A",
                "repeat_start": True,
                "chords": [{"beat": 1.0, "symbol": "C7"}],
            },
            {
                "measure": 2,
                "section": "A",
                "repeat_end": True,
                "chords": [{"beat": 1.0, "symbol": "F7"}],
            },
        ],
    })
    timeline = expand_playback_timeline(song)
    assert [m.source_measure for m in timeline.measures] == [1, 2, 1, 2]
    assert {m.chorus_index for m in timeline.measures} == {1}


def test_shared_session_and_future_harmony_use_playback_timeline():
    song = song_from_normalized_record({
        "realchord_id": "rc_future",
        "title": "Future Tune",
        "measures": [
            {
                "measure": 1,
                "section": "A",
                "chords": [{"beat": 1.0, "symbol": "C^7"}],
            },
            {
                "measure": 2,
                "section": "A",
                "chords": [{"beat": 1.0, "symbol": "D-7"}],
            },
            {
                "measure": 3,
                "section": "B",
                "chords": [{"beat": 1.0, "symbol": "G7"}],
            },
        ],
    })
    timeline = expand_playback_timeline(song)
    state = session_state_at(song, timeline, playback_measure=2, beat=1.0, chorus_index=3)
    assert state.source_measure == 2
    assert state.section == "A"
    assert state.chorus_index == 3
    assert expected_harmony_for_state(song, state).chord_symbol == "D-7"

    future = future_harmony(song, timeline, state, lookahead_measures=1)
    assert future == (
        (2, 2, "A", ("D-7",)),
        (3, 3, "B", ("G7",)),
    )
