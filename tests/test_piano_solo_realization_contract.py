from music_intelligence.reasoning.solo_candidates import SoloCandidateSpec
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent
from players.piano.solo_realizer import PianoSoloRealizer,PianoSoloRealizerContext
from players.piano.feasibility import assess_piano_solo_feasibility,PianoFeasibilityContext

def test_piano_realizes_shared_candidate_in_register():
    r=PianoSoloRealizer().realize(SoloCandidateSpec(0,.5),SoloExpressionIntent(),PianoSoloRealizerContext(low_midi=60,high_midi=72,anchor_midi=66))
    assert 60<=r.event.pitch_midi<=72
    assert r.event.pitch_midi%12==0
    assert assess_piano_solo_feasibility(r,PianoFeasibilityContext(previous_pitch_midi=64)).feasible
