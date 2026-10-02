from players.drums.model import DrummerRuntimeContext, GestureRole
from players.drums.rhythmic_language import engineering_seed_motif
from players.drums.solo import (
    DrumSoloPlan,
    DrumSoloState,
    SoloArc,
    SoloDevelopment,
    build_solo_candidates,
    perform_one_solo_gesture,
)


def candidate_for(candidates, development):
    return next(c for c in candidates if c.development is development)


def test_repeat_candidate_preserves_motif_ioi_identity():
    motif = engineering_seed_motif()
    state = DrumSoloState(
        gestures_committed=3,
        statements=3,
        motif_identity=motif,
    )
    plan = DrumSoloPlan(arc=SoloArc.DEVELOP, adventurousness=0.6)
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0)

    c = candidate_for(build_solo_candidates(plan, ctx, state), SoloDevelopment.REPEAT)

    assert c.motif_identity is not None
    assert c.motif_identity.iois == motif.iois
    assert c.motif_identity.onset_units == motif.onset_units


def test_displace_candidate_changes_real_onset_positions():
    motif = engineering_seed_motif()
    state = DrumSoloState(
        gestures_committed=4,
        statements=4,
        motif_identity=motif,
    )
    plan = DrumSoloPlan(arc=SoloArc.DEVELOP, adventurousness=0.7)
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0)

    c = candidate_for(build_solo_candidates(plan, ctx, state), SoloDevelopment.DISPLACE)

    assert c.motif_identity is not None
    assert c.motif_identity.onset_units != motif.onset_units


def test_orchestrate_candidate_changes_contour_but_not_rhythm():
    motif = engineering_seed_motif()
    state = DrumSoloState(
        gestures_committed=2,
        statements=2,
        motif_identity=motif,
    )
    plan = DrumSoloPlan(arc=SoloArc.DEVELOP, adventurousness=0.5)
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0)

    c = candidate_for(build_solo_candidates(plan, ctx, state), SoloDevelopment.ORCHESTRATE)

    assert c.motif_identity is not None
    assert c.motif_identity.onset_units == motif.onset_units
    assert c.motif_identity.orchestration_contour != motif.orchestration_contour


def test_internal_rest_removes_onset_instead_of_becoming_generic_silence_tag():
    motif = engineering_seed_motif()
    state = DrumSoloState(
        gestures_committed=2,
        statements=2,
        motif_identity=motif,
    )
    plan = DrumSoloPlan(arc=SoloArc.DEVELOP, adventurousness=0.5)
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0)

    c = candidate_for(build_solo_candidates(plan, ctx, state), SoloDevelopment.INTERNAL_REST)

    assert c.motif_identity is not None
    assert len(c.motif_identity.onset_units) == len(motif.onset_units) - 1


def test_performance_commits_one_event_and_remembers_motif_identity():
    state = DrumSoloState()
    plan = DrumSoloPlan(arc=SoloArc.OPEN)
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0)

    chosen = perform_one_solo_gesture(plan, ctx, state)

    assert state.motif_identity is not None
    assert len(chosen.gesture.hits) <= 1
    assert not hasattr(chosen.gesture, "future_hits")


def test_between_motif_onsets_solo_can_deliberately_emit_space():
    motif = engineering_seed_motif()
    state = DrumSoloState(
        gestures_committed=3,
        statements=3,
        motif_identity=motif,
    )
    plan = DrumSoloPlan(arc=SoloArc.DEVELOP, adventurousness=0.6)
    # unit ~= 2 on a 12-unit cycle: between the seed's 0 and 4 onsets.
    ctx = DrummerRuntimeContext(position_in_bar_beats=2.0 / 3.0)

    repeat = candidate_for(build_solo_candidates(plan, ctx, state), SoloDevelopment.REPEAT)

    assert repeat.gesture.role is GestureRole.SPACE
    assert repeat.gesture.hits == ()
