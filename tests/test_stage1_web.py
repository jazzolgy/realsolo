from realtime.ensemble_app.stage1_web import chart_payload, demo_chart
from realtime.ensemble_app.canonical_repertoire import AUTUMN_LEAVES_G_MINOR_JAM


def test_stage1_payload_contains_chart_and_transposition():
    payload = chart_payload(demo_chart(), transpose=2)
    assert payload["title"] == "RealSolo ii–V–I Lab"
    assert payload["bars"][0]["chords"] == ["Em7"]
    assert payload["bars"][1]["chords"] == ["A7"]
    assert payload["choruses"] == 3



def test_autumn_leaves_chart_payload_is_available_for_canonical_quartet_mode():
    payload=chart_payload(AUTUMN_LEAVES_G_MINOR_JAM)
    assert payload["title"].startswith("Autumn Leaves")
    assert payload["tempo_bpm"] == 172.0
    assert len(payload["bars"]) == 32
    assert payload["bars"][0]["chords"] == ["Cm7"]
    assert payload["bars"][26]["chords"] == ["Gm","C7"]
