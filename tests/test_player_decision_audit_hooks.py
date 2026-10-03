import inspect

from music_intelligence.reasoning.decision_context_log import (
    CandidateAudit,
    DecisionContextLog,
    append_ranked_decision,
)
from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    PlayerPresence,
    PlayerRole,
    TransportState,
)
from players.bass.immediate_realizer import choose_immediate_bass_action
from players.drums.online_drummer import perform_one_gesture
from players.piano.comping import perform_one_comping_action
from players.piano.solo import perform_one_piano_solo_event


def _state():
    return EnsembleState(
        transport=TransportState(beat=0.0, bar=1),
        players=(
            PlayerPresence("piano", "piano", PlayerRole.COMPER),
            PlayerPresence("bass", "bass", PlayerRole.BASS),
            PlayerPresence("drums", "drum_set", PlayerRole.DRUMS),
        ),
    )


def test_generic_append_ranked_decision_records_shared_context():
    log=DecisionContextLog()
    state=_state()
    record=append_ranked_decision(
        log,
        player_id="piano",
        decision_kind="solo",
        ensemble_state=state,
        candidates=(
            CandidateAudit("a",.1,{"legend:passing":.02}),
            CandidateAudit("b",.2,{"harmonic_identity":.1}),
        ),
        selected_candidate_id="b",
        selected_score=.2,
        contextual_gate_weights={"legend":.4},
        reasons=("selected by evaluator",),
        provenance=("test",),
    )

    assert record is not None
    assert record.context is not None
    assert record.context.bar == 1
    assert record.selected_candidate_id == "b"
    assert record.contextual_gate_weights["legend"] == .4
    assert record.prior_contributions == {}


def test_none_log_keeps_runtime_hook_optional():
    record=append_ranked_decision(
        None,
        player_id="bass",
        decision_kind="bass_immediate",
        ensemble_state=None,
        candidates=(CandidateAudit("bass:0",.5),),
        selected_candidate_id="bass:0",
        selected_score=.5,
    )
    assert record is None


def test_player_commit_paths_expose_same_optional_audit_hooks():
    for function in (
        perform_one_piano_solo_event,
        perform_one_comping_action,
        choose_immediate_bass_action,
        perform_one_gesture,
    ):
        params=inspect.signature(function).parameters
        assert "decision_log" in params
        assert "ensemble_state" in params
        assert "player_id" in params
