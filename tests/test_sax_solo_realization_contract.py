from music_intelligence.reasoning.solo_candidates import SoloCandidateSpec
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent
from players.sax.solo_realizer import SaxSoloRealizer,SaxSoloRealizerContext
from players.sax.feasibility import assess_sax_solo_feasibility
from players.sax.physical import SaxPhysicalConstraints

def test_sax_realizes_shared_solo_candidate_and_feasibility():
    r=SaxSoloRealizer().realize(SoloCandidateSpec(2,.5),SoloExpressionIntent(),SaxSoloRealizerContext(low_midi=50,high_midi=86))
    a=assess_sax_solo_feasibility(r,previous_pitch_midi=62,notes_since_breath=2,beats_since_breath=2.0,constraints=SaxPhysicalConstraints(50,86,7,20,16.0))
    assert r.event.pitch_midi%12==2
    assert a.feasible
