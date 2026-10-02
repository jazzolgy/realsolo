from music_intelligence.reasoning.turn_taking import TurnTakingEvidence,TurnTakingType
from music_intelligence.reasoning.ensemble_complementarity import EnsembleComplementarityEvidence
from music_intelligence.reasoning.harmonic_turn import HarmonicTurnContext,HarmonicTurnPhase
from music_intelligence.reasoning.solo_phrase_intent import derive_solo_phrase_intent
from music_intelligence.reasoning.solo_candidates import generate_solo_candidate_specs
from music_intelligence.reasoning.solo_grammar import SoloDevelopmentOperation

def test_shared_solo_intent_is_not_bebop_or_piano_owned():
    intent=derive_solo_phrase_intent(
        HarmonicTurnContext(phase=HarmonicTurnPhase.ANTICIPATORY,anticipation_strength=.8,confidence=.8),
        TurnTakingEvidence(TurnTakingType.AMBIGUOUS,1,1,1,1,.5,0),
        EnsembleComplementarityEvidence(),
    )
    assert intent.target_mode.value=="next_harmony"
    assert isinstance(intent.solo_method,SoloDevelopmentOperation)

def test_shared_candidate_specs_have_no_instrument_register():
    from music_intelligence.reasoning.solo_phrase_intent import SoloPhraseIntent,SoloEntryMode,SoloTargetMode,SoloDensityDirection
    intent=SoloPhraseIntent(2,SoloEntryMode.CONTINUE,SoloTargetMode.GUIDE_TONE,SoloDensityDirection.STABLE,("passing",))
    specs=generate_solo_candidate_specs(intent=intent,structural_pitch_classes=frozenset({0,4,7}))
    assert specs
    assert all(s.pitch_class is None or 0<=s.pitch_class<=11 for s in specs)
    assert all(not hasattr(s,"pitch_midi") for s in specs)
