from music_intelligence.corpus import (
    RealChordChord,
    RealChordMeasure,
    RealChordRawSong,
    RealChordSong,
    expand_playback_timeline,
    expected_harmony_for_state,
    future_harmony,
    library_from_normalized_corpus,
    normalize_raw_song,
    parse_progression,
    parse_realchord_playlist_html,
    session_state_at,
    song_from_normalized_record,
)


def _hussle(value: str) -> str:
    text = value
    result = ""
    while len(text) > 50:
        segment = text[:50]
        text = text[50:]
        if len(text) < 2:
            result += segment
            continue
        result += (
            segment[45:50][::-1]
            + segment[5:10]
            + segment[26:40][::-1]
            + segment[24:26]
            + segment[10:24][::-1]
            + segment[40:45]
            + segment[0:5][::-1]
        )
    return result + text


def _encode_for_test(plain: str) -> str:
    text = plain.replace("   ", "XyQ").replace(" |", "LZ").replace("| x", "Kcl")
    return "1r34LbKcu7" + _hussle(text)


def test_raw_ingestion_accepts_trailing_playlist_name_and_preserves_numeric_ids():
    html = (
        '<a href="irealb://'
        'One=Composer==Swing=C==RAW1==0=0==='
        'Two=Composer==Swing=F==RAW2==0=0==='
        'RealChord%202'
        '">x</a>'
    )
    rows = parse_realchord_playlist_html(html)
    assert [row.realchord_id for row in rows] == ["1", "2"]
    assert [row.title for row in rows] == ["One", "Two"]


def test_structural_parser_keeps_existing_realchord_identity():
    plain = "*A[T44C^7   |D-7 G7 Z"
    raw = RealChordRawSong(
        realchord_id="96",
        source_index=96,
        title="Autumn Leaves",
        composer="Kosma Joseph",
        style="Medium Swing",
        key="G-",
        raw_chart=_encode_for_test(plain),
    )
    record = normalize_raw_song(raw)
    assert record["realchord_id"] == "96"
    assert len(record["measures"]) == 2
    assert record["measures"][0]["section"] == "A"
    assert record["measures"][0]["chords"][0]["symbol"] == "C^7"
    assert [x["symbol"] for x in record["measures"][1]["chords"]] == ["D-7", "G7"]


def test_adapter_accepts_canonical_expected_harmony_shape():
    song = song_from_normalized_record({
        "realchord_id": "96",
        "title": "Autumn Leaves",
        "canonical": {
            "measures": [
                {
                    "measure": 1,
                    "section": "A",
                    "expected_harmony": [
                        {"beat": 1.0, "symbol": "C-7", "confidence": 0.95},
                        {"beat": 3.0, "symbol": "F7", "confidence": 0.95},
                    ],
                }
            ]
        },
    })
    assert [chord.symbol for chord in song.measure_at(1).chords] == ["C-7", "F7"]


def test_internal_repeat_is_one_form_pass_not_a_new_chorus():
    song = RealChordSong(
        realchord_id="repeat",
        title="Repeat Tune",
        measures=(
            RealChordMeasure(
                measure=1,
                section="A",
                repeat_start=True,
                chords=(RealChordChord(beat=1.0, symbol="C7"),),
            ),
            RealChordMeasure(
                measure=2,
                section="A",
                repeat_end=True,
                chords=(RealChordChord(beat=1.0, symbol="F7"),),
            ),
        ),
    )
    timeline = expand_playback_timeline(song)
    assert [item.source_measure for item in timeline.measures] == [1, 2, 1, 2]


def test_shared_library_session_and_future_harmony_use_one_chart():
    library = library_from_normalized_corpus({
        "songs": [
            {
                "realchord_id": "shared",
                "title": "Shared Tune",
                "measures": [
                    {
                        "measure": 1,
                        "section": "A",
                        "chords": [{"beat": 1.0, "symbol": "C^7"}],
                    },
                    {
                        "measure": 2,
                        "section": "B",
                        "chords": [{"beat": 1.0, "symbol": "G7"}],
                    },
                ],
            }
        ]
    })
    song = library.get("shared")
    timeline = expand_playback_timeline(song)
    state = session_state_at(
        song,
        timeline,
        playback_measure=1,
        beat=1.0,
        chorus_index=3,
        tempo=144,
    )
    assert state.chorus_index == 3
    assert expected_harmony_for_state(song, state).chord_symbol == "C^7"
    assert future_harmony(song, timeline, state, lookahead_measures=1) == (
        (1, 1, "A", ("C^7",)),
        (2, 2, "B", ("G7",)),
    )
