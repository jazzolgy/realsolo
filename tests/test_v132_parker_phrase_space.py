import json
from pathlib import Path

from music_intelligence.bebop.parker_v132_blend import PARKER_V132_BLEND
from music_intelligence.reasoning.legend_style_core import CandidateEvent, MusicalContextVector
from music_intelligence.reasoning.online_improviser import OnlineMusicalEvaluator


def _data():
    path = (
        Path(__file__).parents[1]
        / "src"
        / "music_intelligence"
        / "legends"
        / "parker"
        / "data"
        / "phrase_space_stats.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_phrase_space_distribution_regression():
    d = _data()
    a = d["aggregate"]
    assert d["source"]["rest_boundaries_analyzed"] == 1461
    assert 0.37 < a["rest_half_beat"]["share"] < 0.38
    assert 0.44 <= a["rest_one_beat"]["share"] < 0.45
    assert 0.16 < a["rest_two_beats"]["share"] < 0.17
    assert 0.02 < a["rest_four_beats"]["share"] < 0.03
    assert a["rest_ge_two_beats_share"] > 0.18


def test_space_profile_rewards_multiple_valid_rest_scales():
    ev = OnlineMusicalEvaluator(PARKER_V132_BLEND)
    ctx = MusicalContextVector(ensemble_activity=.75, phrase_maturity=.8)
    half = ev.evaluate(CandidateEvent(None, .5, tags=frozenset({"ensemble_space"})), ctx)
    one = ev.evaluate(CandidateEvent(None, 1.0, tags=frozenset({"ensemble_space"})), ctx)
    two = ev.evaluate(CandidateEvent(None, 2.0, tags=frozenset({"ensemble_space"})), ctx)
    assert half.total > 0
    assert one.total > 0
    assert two.total > 0
    assert "legend:rest_half_beat" in half.components
    assert "legend:rest_one_beat" in one.components
    assert "legend:rest_two_beats" in two.components


def test_rest_is_one_immediate_candidate_not_future_sequence():
    event = CandidateEvent(None, 2.0, tags=frozenset({"ensemble_space"}))
    assert event.pitch_midi is None
    assert event.duration_beats == 2.0


def test_benchmark_variation_prevents_tempo_only_space_rule():
    d = _data()["benchmarks"]
    assert d["Ko Ko"]["two_beat_share"] > d["Confirmation"]["two_beat_share"]
    assert d["Ko Ko"]["four_beat_share"] > d["Confirmation"]["four_beat_share"]
