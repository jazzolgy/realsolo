import pytest
from music_intelligence.reasoning.legend_style_core import *
from music_intelligence.reasoning.online_improviser import *

def test_slow_brain_cannot_freeze_future_note_sequence():
    p=SoftPlan(8,"build tension", exact_future_notes=(60,62,64))
    with pytest.raises(ValueError):
        p.validate_for_improvisation()

def test_runtime_commits_only_one_event():
    memory=PerformanceMemory()
    ev=OnlineMusicalEvaluator()
    p=SoftPlan(4,"continue",soft_targets=("3rd",),candidate_families=("bebop_connector",))
    ctx=MusicalContextVector(phrase_maturity=.2)
    cs=[CandidateEvent(60,.5,tags=frozenset({"chord_tone"})),
        CandidateEvent(61,.5,tags=frozenset({"passing"}))]
    perform_one_event(p,ev,cs,ctx,memory)
    assert len(memory.committed)==1

def test_altered_chain_is_not_hard_banned():
    ev=OnlineMusicalEvaluator()
    ctx=MusicalContextVector(recent_altered_density=.8,recent_chord_identity_strength=.7)
    c=CandidateEvent(61,.5,tags=frozenset({"altered","directed_target"}))
    assert ev.evaluate(c,ctx).total > 0

def test_obscured_undirected_altered_color_gets_soft_penalty():
    ev=OnlineMusicalEvaluator()
    ctx=MusicalContextVector(recent_altered_density=.9,recent_chord_identity_strength=.1)
    c=CandidateEvent(61,.5,tags=frozenset({"altered"}))
    assert ev.evaluate(c,ctx).components["identity_occlusion"] < 0

def test_legend_blend_operates_on_tendencies_not_phrase_splices():
    t=StyleTendency("t1","anticipation",frozenset({"anticipation"}),.5,1.0)
    p=LegendProfile("x","X","sax","bebop",(t,))
    b=LegendBlend(((p,.4),))
    assert b.feature_bias("anticipation",("anticipation",)) == pytest.approx(.2)

def test_parker_profile_biases_policy_not_future_notes():
    from music_intelligence.bebop.parker_online_profile import PARKER_ONLINE_PROFILE
    b=LegendBlend(((PARKER_ONLINE_PROFILE,1.0),))
    assert b.feature_bias("anticipation",("anticipation",)) > 0
    assert not hasattr(PARKER_ONLINE_PROFILE,"exact_future_notes")
