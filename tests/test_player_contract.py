from realtime.ensemble_app.player_contract import (
    fallback_accompaniment_gesture,
    monophonic_solo_gesture,
)


def test_fallback_frame_becomes_renderer_gesture():
    gesture = fallback_accompaniment_gesture(
        {
            "bass": [38],
            "comp": [60, 65, 69],
            "drums": {"ride": True, "hat": False, "kick": True},
        }
    )
    payload = gesture.to_dict()
    assert payload["source"] == "realtime_fallback"
    assert [v["instrument_role"] for v in payload["voices"]] == [
        "bass", "piano", "piano", "piano"
    ]
    assert {v["pitch_midi"] for v in payload["drum_hits"]} == {36, 51}


def test_solo_contract_commits_one_renderer_voice():
    payload = monophonic_solo_gesture(67, 0.5).to_dict()
    assert payload["role"] == "soloist"
    assert len(payload["voices"]) == 1
    assert payload["voices"][0]["pitch_midi"] == 67
