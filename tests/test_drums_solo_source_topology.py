from players.drums.model import DrummerRuntimeContext
from players.drums.solo import DrumSoloPlan, DrumSoloState, build_solo_candidates


def first_motif(cell_id):
    plan = DrumSoloPlan(motif_cell_id=cell_id)
    state = DrumSoloState()
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0)
    candidates = build_solo_candidates(plan, ctx, state)
    return next(c.motif_identity for c in candidates if c.motif_identity is not None)


def test_source_cells_seed_distinct_nonliteral_topologies():
    three = first_motif("riley_three_beat_cycle")
    group4 = first_motif("beyond_bop_triplets_groups_of_four")
    five = first_motif("unreel_america_5_5_5_6")

    assert three.cycle_units == 3
    assert three.onset_units == (0, 1, 2)

    assert group4.cycle_units == 4
    assert group4.onset_units == (0, 1, 2, 3)

    assert five.cycle_units == 21
    assert five.onset_units == (0, 5, 10, 15)


def test_source_topology_is_group_boundary_not_full_future_phrase():
    five = first_motif("unreel_america_5_5_5_6")
    assert five.source == "unreel_grouping_boundaries_only"
    assert not hasattr(five, "future_hits")
    assert not hasattr(five, "literal_phrase")
