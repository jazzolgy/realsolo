from music_intelligence.drums.model import DrummerRuntimeContext, GestureRole
from music_intelligence.drums.solo import (
    DrumSoloPlan,
    DrumSoloState,
    SoloArc,
    SoloDevelopment,
    SOLO_VOCABULARY,
    build_solo_candidates,
    perform_one_solo_gesture,
    solo_cell,
)


def test_solo_vocabulary_contains_source_derived_advanced_cells():
    ids = {c.cell_id for c in SOLO_VOCABULARY}
    assert "riley_three_beat_cycle" in ids
    assert "beyond_bop_triplets_groups_of_four" in ids
    assert "unreel_america_5_5_5_6" in ids


def test_solo_opens_with_clear_statement_not_immediate_metric_trick():
    plan = DrumSoloPlan(arc=SoloArc.OPEN, adventurousness=0.9)
    state = DrumSoloState()
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0)

    chosen = perform_one_solo_gesture(plan, ctx, state)

    assert chosen.development is SoloDevelopment.STATE
    assert chosen.gesture.role is GestureRole.FILL


def test_solo_develops_after_initial_statement():
    plan = DrumSoloPlan(arc=SoloArc.DEVELOP, adventurousness=0.55)
    state = DrumSoloState(statements=2, gestures_committed=2)
    ctx = DrummerRuntimeContext(position_in_bar_beats=1.0)

    candidates = build_solo_candidates(plan, ctx, state)
    devs = {c.development for c in candidates}

    assert SoloDevelopment.ORCHESTRATE in devs
    assert SoloDevelopment.DISPLACE in devs
    assert SoloDevelopment.THREE_BEAT_CYCLE in devs


def test_advanced_metric_illusion_requires_higher_adventurousness():
    ctx = DrummerRuntimeContext(position_in_bar_beats=2.0)
    state = DrumSoloState(statements=4, gestures_committed=4)

    safe = build_solo_candidates(DrumSoloPlan(adventurousness=0.3), ctx, state)
    adventurous = build_solo_candidates(DrumSoloPlan(adventurousness=0.9), ctx, state)

    assert SoloDevelopment.METRIC_ILLUSION not in {c.development for c in safe}
    assert SoloDevelopment.METRIC_ILLUSION in {c.development for c in adventurous}


def test_solo_reentry_becomes_high_priority_near_transition():
    plan = DrumSoloPlan(
        arc=SoloArc.REENTRY,
        target_reentry=True,
        adventurousness=0.5,
    )
    state = DrumSoloState(statements=6, gestures_committed=7)
    ctx = DrummerRuntimeContext(
        position_in_bar_beats=3.0,
        phrase_position=0.97,
        section_transition=True,
    )

    chosen = perform_one_solo_gesture(plan, ctx, state)

    assert chosen.development is SoloDevelopment.RESOLVE


def test_unreel_asymmetric_grouping_is_preserved():
    cell = solo_cell("unreel_america_5_5_5_6")
    assert cell.grouping == (5, 5, 5, 6)
    assert cell.exact_structural_pattern is True
