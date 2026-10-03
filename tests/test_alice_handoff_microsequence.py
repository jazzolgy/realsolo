import json
from pathlib import Path

from music_intelligence.reasoning.musical_moment import (
    MomentActionCommitment,
    MomentPhraseState,
    MomentPlayerAction,
    MomentPosition,
    MusicalMoment,
)


DATA=(
    Path(__file__).resolve().parents[1]
    / "research" / "legends" / "scott_lafaro" / "observations" / "moments"
    / "alice_A13_18_handoff_microsequence_v0_1.json"
)


def _moment(raw):
    return MusicalMoment(
        moment_id=raw["moment_id"],
        position=MomentPosition(**raw["position"]),
        phrase=MomentPhraseState(
            phrase_id=raw["phrase"]["phrase_id"],
            phrase_position=raw["phrase"]["phrase_position"],
            maturity=raw["phrase"]["maturity"],
            boundary_pressure=raw["phrase"]["boundary_pressure"],
            space=raw["phrase"]["space"],
            tension=raw["phrase"]["tension"],
            motif_id=raw["phrase"]["motif_id"],
            confidence=raw["phrase"]["confidence"],
            provenance=tuple(raw["phrase"]["provenance"]),
        ),
        player_actions=tuple(
            MomentPlayerAction(
                player_id=x["player_id"],
                instrument=x["instrument"],
                role=x["role"],
                action_type=x["action_type"],
                interaction=x["interaction"],
                commitment=MomentActionCommitment(x["commitment"]),
                density=x["density"],
                energy=x["energy"],
                tension=x["tension"],
                space=x["space"],
                register_center=x["register_center"],
                phrase_role=x["phrase_role"],
                motif_id=x["motif_id"],
                semantic_tags=frozenset(x["semantic_tags"]),
                confidence=x["confidence"],
                provenance=tuple(x["provenance"]),
                metadata=x["metadata"],
            ) for x in raw["player_actions"]
        ),
        confidence=raw["confidence"],
        provenance=tuple(raw["provenance"]),
    )


def test_alice_handoff_microsequence_is_ordered_and_valid():
    payload=json.loads(DATA.read_text(encoding="utf-8"))
    assert payload["sequence_semantics"]["ordered"] is True
    assert payload["sequence_semantics"]["causal"] is False
    assert payload["sequence_semantics"]["reward"] is False

    moments=[_moment(x) for x in payload["moments"]]
    assert len(moments) == 5
    for moment in moments:
        moment.validate()

    assert [x["order"] for x in payload["moments"]] == [1,2,3,4,5]


def test_alice_handoff_tracks_support_foreground_support_without_pitch_commands():
    payload=json.loads(DATA.read_text(encoding="utf-8"))
    moments=payload["moments"]

    first_bass=next(x for x in moments[0]["player_actions"] if x["player_id"]=="bass")
    entry_bass=next(x for x in moments[2]["player_actions"] if x["player_id"]=="bass")
    develop_bass=next(x for x in moments[3]["player_actions"] if x["player_id"]=="bass")
    final_bass=next(x for x in moments[4]["player_actions"] if x["player_id"]=="bass")

    assert first_bass["role"] == "support"
    assert entry_bass["role"] == "foreground"
    assert develop_bass["role"] == "foreground"
    assert final_bass["role"] == "support"

    assert "longer_values" in first_bass["semantic_tags"]
    assert "low_register" in first_bass["semantic_tags"]
    assert "foreground_entry" in entry_bass["semantic_tags"]
    assert "eighth_notes" in entry_bass["semantic_tags"]
    assert "upper_register" in develop_bass["semantic_tags"]
    assert "register_descent" in final_bass["semantic_tags"]
    assert "support_return" in final_bass["semantic_tags"]

    # Literature prose supports qualitative direction, not precise 0..1 values.
    for action in (first_bass, entry_bass, develop_bass, final_bass):
        assert action["density"] is None
        assert action["energy"] is None
        assert action["tension"] is None
        assert action["space"] is None
        assert action["register_center"] is None

    raw=json.dumps(payload).lower()
    assert "pitch_midi" not in raw
    assert "literal_representation" not in raw
    assert "voicing" not in raw


def test_piano_space_and_reentry_are_temporal_observations_not_causal_fields():
    payload=json.loads(DATA.read_text(encoding="utf-8"))
    space=payload["moments"][1]
    reentry=payload["moments"][4]

    piano_space=next(x for x in space["player_actions"] if x["player_id"]=="piano")
    piano_reentry=next(x for x in reentry["player_actions"] if x["player_id"]=="piano")

    assert piano_space["action_type"] == "phrase_resolution_then_space"
    assert piano_space["space"] is None
    assert "space_opening" in piano_space["semantic_tags"]
    assert piano_reentry["action_type"] == "new_phrase_entry"

    raw=json.dumps(payload).lower()
    assert "caused_by" not in raw
    assert "because" not in raw
    assert all("sequence_order_only_not_causal" in x["provenance"] for x in payload["moments"])


def test_microsequence_keeps_drums_unknown_until_supported():
    payload=json.loads(DATA.read_text(encoding="utf-8"))
    assert all(
        all(action["player_id"] != "drums" for action in moment["player_actions"])
        for moment in payload["moments"]
    )
    assert "drum-set behavior in this micro-sequence" in payload["unresolved"]
