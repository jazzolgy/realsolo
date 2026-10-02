from players.drums.model import DrummerRuntimeContext
from players.drums.rhythmic_language import (
    CommittedRhythmicEvent,
    engineering_seed_motif,
    motif_from_committed_events,
)
from players.drums.solo import DrumSoloPlan, DrumSoloState, SoloArc, perform_one_solo_gesture


def test_solo_retrospective_motif_requires_committed_evidence():
    one = (CommittedRhythmicEvent(unit=0, accent=0.8, orchestration_slot=0),)
    assert motif_from_committed_events(one) is None


def test_solo_retrospective_motif_uses_only_played_onsets():
    events = (
        CommittedRhythmicEvent(unit=0, accent=0.8, orchestration_slot=0),
        CommittedRhythmicEvent(unit=4, accent=0.5, orchestration_slot=1),
        CommittedRhythmicEvent(unit=7, accent=0.7, orchestration_slot=2),
    )
    motif = motif_from_committed_events(events)
    assert motif is not None
    assert motif.onset_units == (0, 4, 7)
    assert motif.source == "retrospective_local_execution"


def test_solo_state_can_replace_seed_with_committed_motif():
    state = DrumSoloState(motif_identity=engineering_seed_motif())
    plan = DrumSoloPlan(arc=SoloArc.OPEN)

    for beat in (0.0, 4.0 / 3.0):
        ctx = DrummerRuntimeContext(position_in_bar_beats=beat, beats_per_bar=4)
        perform_one_solo_gesture(plan, ctx, state)

    assert state.motif_identity is not None
    if len(state.committed_rhythmic_events) >= 2:
        assert state.motif_identity.source == "retrospective_local_execution"


def test_solo_commit_remains_one_event_at_a_time():
    state = DrumSoloState()
    plan = DrumSoloPlan(arc=SoloArc.OPEN)
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0)

    chosen = perform_one_solo_gesture(plan, ctx, state)

    assert len(chosen.gesture.hits) <= 1
    assert not hasattr(state, "future_phrase")
