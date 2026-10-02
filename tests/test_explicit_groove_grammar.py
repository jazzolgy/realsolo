from music_intelligence.learning import DEFAULT_GROOVE_GRAMMARS,best_matching_grammars,groove_similarity

def density(total,slots):
    out=[0.0]*total
    for s in slots: out[s]=1.0
    return tuple(out)

def test_son_clave_2_3_exact_match():
    g=next(x for x in DEFAULT_GROOVE_GRAMMARS if x.grammar_id=="salsa.son_clave.2_3")
    d=density(32,g.onset_slots)
    assert groove_similarity(d,g)==1.0
    assert best_matching_grammars(d,cycle_beats=8.0,subdivisions_per_beat=4)[0][0].grammar_id=="salsa.son_clave.2_3"

def test_funk_16th_exact_match():
    g=next(x for x in DEFAULT_GROOVE_GRAMMARS if x.grammar_id=="funk.16th_pocket")
    d=density(16,g.onset_slots)
    best=best_matching_grammars(d,cycle_beats=4.0,subdivisions_per_beat=4)
    assert best[0][0].grammar_id=="funk.16th_pocket"
    assert best[0][1]==1.0

def test_triplet_grid_for_swing():
    g=next(x for x in DEFAULT_GROOVE_GRAMMARS if x.grammar_id=="swing.eighth_triplet_feel")
    d=density(12,g.onset_slots)
    best=best_matching_grammars(d,cycle_beats=4.0,subdivisions_per_beat=3)
    assert best and all(x[0].subdivisions_per_beat==3 for x in best)
