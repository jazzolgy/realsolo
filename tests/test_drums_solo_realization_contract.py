from music_intelligence.reasoning.solo_candidates import SoloCandidateSpec
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent
from players.drums.solo_realizer import DrumSoloRealizer,DrumSoloRealizerContext
from players.drums.feasibility import assess_drum_solo_feasibility

def test_drums_realize_rhythm_only_shared_solo_candidate():
    r=DrumSoloRealizer().realize(SoloCandidateSpec(None,.5,tags=frozenset({"rhythmic_displacement"})),SoloExpressionIntent(accent=.8),DrumSoloRealizerContext())
    assert r.gesture.hits
    assert assess_drum_solo_feasibility(r).feasible

def test_drums_realize_shared_space():
    r=DrumSoloRealizer().realize(SoloCandidateSpec(None,.5,tags=frozenset({"rest"})),SoloExpressionIntent(),DrumSoloRealizerContext())
    assert not r.gesture.hits
