from realtime.ensemble_app.stage1_web import chart_payload, demo_chart


def test_stage1_payload_contains_chart_and_transposition():
    payload = chart_payload(demo_chart(), transpose=2)
    assert payload["title"] == "RealSolo ii–V–I Lab"
    assert payload["bars"][0]["chords"] == ["Em7"]
    assert payload["bars"][1]["chords"] == ["A7"]
    assert payload["choruses"] == 3
