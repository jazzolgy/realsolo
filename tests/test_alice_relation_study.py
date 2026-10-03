import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1] / "research" / "legends" / "scott_lafaro"
MOMENTS=ROOT / "observations" / "moments"
REL=ROOT / "analyses" / "alice_musical_moment_relation_candidates_v0_1.json"


def _load(name):
    return json.loads((MOMENTS / name).read_text(encoding="utf-8"))


def test_alice_mimesis_sequence_preserves_order_without_causal_claim():
    payload=_load("alice_A37_39_mimesis_microsequence_v0_1.json")
    assert payload["sequence_semantics"]["ordered"] is True
    assert payload["sequence_semantics"]["causal"] is False
    assert [x["order"] for x in payload["moments"]] == [1,2,3,4,5]
    raw=json.dumps(payload).lower()
    assert "caused_by" not in raw
    assert "reward" in payload["sequence_semantics"] and payload["sequence_semantics"]["reward"] is False


def test_alice_mimesis_sequence_tracks_shape_match_and_support_return():
    payload=_load("alice_A37_39_mimesis_microsequence_v0_1.json")
    simultaneous=payload["moments"][2]
    delayed=payload["moments"][3]
    final=payload["moments"][4]

    bass_sim=next(x for x in simultaneous["player_actions"] if x["player_id"]=="bass")
    bass_delayed=next(x for x in delayed["player_actions"] if x["player_id"]=="bass")
    bass_final=next(x for x in final["player_actions"] if x["player_id"]=="bass")

    assert "shared_rhythm_shape" in bass_sim["semantic_tags"]
    assert "shared_contour_shape" in bass_sim["semantic_tags"]
    assert "one_beat_delayed" in bass_delayed["semantic_tags"]
    assert bass_final["role"] == "support"
    assert "support_return" in bass_final["semantic_tags"]


def test_alice_45_47_sequence_represents_subdivision_and_contour_change_qualitatively():
    payload=_load("alice_A45_47_contour_response_microsequence_v0_1.json")
    pre=payload["moments"][0]
    piano_change=payload["moments"][1]
    bass_change=payload["moments"][2]
    continuation=payload["moments"][3]
    resolution=payload["moments"][4]

    pre_bass=next(x for x in pre["player_actions"] if x["player_id"]=="bass")
    piano=next(x for x in piano_change["player_actions"] if x["player_id"]=="piano")
    bass=next(x for x in bass_change["player_actions"] if x["player_id"]=="bass")

    assert {"low_register","quarter_or_half_notes"} <= set(pre_bass["semantic_tags"])
    assert {"ascending","eighth_notes","subdivision_change"} <= set(piano["semantic_tags"])
    assert {"activity_increase","ascending","eighth_notes","contour_match"} <= set(bass["semantic_tags"])
    assert "polyrhythm" in continuation["player_actions"][0]["semantic_tags"]
    assert "beat_one_resolution" in resolution["player_actions"][0]["semantic_tags"]

    for moment in payload["moments"]:
        for action in moment["player_actions"]:
            assert action["density"] is None
            assert action["energy"] is None
            assert action["tension"] is None
            assert action["space"] is None
            assert action["register_center"] is None


def test_relation_study_keeps_recurrence_separate_from_causal_or_legend_promotion():
    payload=json.loads(REL.read_text(encoding="utf-8"))
    assert len(payload["sequences"]) == 3
    assert all(x["status"] == "relation_candidate" for x in payload["recurrent_observations"])
    assert all(x["promotion_status"] == "not_promoted" for x in payload["legend_hypotheses"])
    assert payload["negative_controls_required"]
    assert "Cross-recording evidence" in payload["promotion_rule"]

    raw=json.dumps(payload).lower()
    assert "the piano event caused the bass change" in raw
    assert "does_not_claim" in raw


def test_relation_study_requires_negative_controls_against_confirmation_bias():
    payload=json.loads(REL.read_text(encoding="utf-8"))
    controls=payload["negative_controls_required"]
    assert any("piano" not in x.lower() or "evans" in x.lower() for x in controls)
    assert any("LaFaro becomes active without" in x for x in controls)
    assert any("another bassist" in x for x in controls)
