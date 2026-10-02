from music_intelligence.reasoning.solo_candidates import SoloCandidateSpec
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent
from players.bass.solo_realizer import BassSoloRealizer,BassSoloRealizerContext
from players.bass.feasibility import assess_bass_solo_feasibility,BassFeasibilityContext

def test_bass_realizes_shared_solo_candidate():
    r=BassSoloRealizer().realize(SoloCandidateSpec(7,1.0),SoloExpressionIntent(),BassSoloRealizerContext(low_midi=31,high_midi=55,anchor_midi=43))
    assert r.event.pitch_midi%12==7
    assert assess_bass_solo_feasibility(r,BassFeasibilityContext(previous_pitch_midi=43,low_midi=31,high_midi=55)).feasible
