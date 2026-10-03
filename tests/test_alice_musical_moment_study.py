import json
from pathlib import Path

from music_intelligence.reasoning.musical_moment import (
    MomentActionCommitment,
    MomentGrooveState,
    MomentHarmony,
    MomentInteraction,
    MomentPhraseState,
    MomentPlayerAction,
    MomentPosition,
    MusicalMoment,
)


DATA = (
    Path(__file__).resolve().parents[1]
    / "research"
    / "legends"
    / "scott_lafaro"
    / "observations"
    / "moments"
    / "alice_in_wonderland_musical_moments_v0_1.json"
)


def _moment(raw):
    return MusicalMoment(
        moment_id=raw["moment_id"],
        position=MomentPosition(**raw["position"]),
        harmony=MomentHarmony(
            expected_ref=raw["harmony"]["expected_ref"],
            observed_ref=raw["harmony"]["observed_ref"],
            inferred_ref=raw["harmony"]["inferred_ref"],
            local_key_ref=raw["harmony"]["local_key_ref"],
            cadence_state=raw["harmony"]["cadence_state"],
            tension=raw["harmony"]["tension"],
            confidence=raw["harmony"]["confidence"],
            provenance=tuple(raw["harmony"]["provenance"]),
        ),
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
        groove=MomentGrooveState(
            grammar_id=raw["groove"]["grammar_id"],
            feel=raw["groove"]["feel"],
            strength=raw["groove"]["strength"],
            confidence=raw["groove"]["confidence"],
            provenance=tuple(raw["groove"]["provenance"]),
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
            )
            for x in raw["player_actions"]
        ),
        interactions=tuple(
            MomentInteraction(
                source_player_id=x["source_player_id"],
                kind=x["kind"],
                target_player_ids=tuple(x["target_player_ids"]),
                confidence=x["confidence"],
                tags=frozenset(x["tags"]),
                provenance=tuple(x["provenance"]),
            )
            for x in raw["interactions"]
        ),
        ensemble_density=raw["ensemble_density"],
        ensemble_energy=raw["ensemble_energy"],
        ensemble_tension=raw["ensemble_tension"],
        space_available=raw["space_available"],
        leader_player_id=raw["leader_player_id"],
        confidence=raw["confidence"],
        provenance=tuple(raw["provenance"]),
        source_refs=tuple(raw["source_refs"]),
    )


def test_alice_study_moments_validate_against_shared_contract():
    payload=json.loads(DATA.read_text(encoding="utf-8"))
    moments=tuple(_moment(x) for x in payload["moments"])
    assert len(moments) == 4
    for moment in moments:
        moment.validate()


def test_alice_study_preserves_partial_observation_instead_of_inventing_trio_actions():
    payload=json.loads(DATA.read_text(encoding="utf-8"))
    moments=tuple(_moment(x) for x in payload["moments"])

    bass_focused=moments[:3]
    assert all({x.player_id for x in m.player_actions} == {"bass"} for m in bass_focused)

    handoff=moments[3]
    assert {x.player_id for x in handoff.player_actions} == {"piano","bass"}
    assert all(x.player_id != "drums" for x in handoff.player_actions)


def test_alice_study_contains_no_literal_note_or_player_realization_payload():
    payload=json.loads(DATA.read_text(encoding="utf-8"))
    serialized=json.dumps(payload).lower()
    forbidden=(
        "pitch_midi",
        "pitch_class",
        "voicing",
        "string_number",
        "fret",
        "ride_hit",
        "snare_hit",
        "kick_hit",
        "render_event",
        "literal_representation",
    )
    assert all(x not in serialized for x in forbidden)


def test_alice_study_does_not_claim_unverified_absolute_audio_alignment():
    payload=json.loads(DATA.read_text(encoding="utf-8"))
    assert any(
        "absolute audio timestamps" in item
        for item in payload["open_questions"]
    )
    for moment in payload["moments"]:
        assert not any("timestamp:" in ref for ref in moment["source_refs"])


def test_space_handoff_is_recorded_as_observed_relation_not_causal_claim():
    payload=json.loads(DATA.read_text(encoding="utf-8"))
    raw=payload["moments"][3]
    assert raw["interactions"][0]["kind"] == "answer"
    assert "observed_relation" in raw["interactions"][0]["tags"]
    serialized=json.dumps(raw).lower()
    assert "caused_by" not in serialized
    assert "because" not in serialized
