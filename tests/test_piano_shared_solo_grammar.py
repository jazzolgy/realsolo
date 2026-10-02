from music_intelligence.reasoning.solo_grammar import SoloDevelopmentOperation
from players.piano.bebop_complementarity import EnsembleComplementarityEvidence
from players.piano.bebop_harmonic_turn import BebopHarmonicTurnContext
from players.piano.bebop_phrase_intent import derive_bebop_phrase_intent
from players.piano.bebop_turn_taking import BebopTurnTakingEvidence, BebopTurnTakingType


def test_piano_phrase_intent_carries_shared_solo_operation():
    intent = derive_bebop_phrase_intent(
        BebopHarmonicTurnContext(),
        BebopTurnTakingEvidence(
            BebopTurnTakingType.AMBIGUOUS,
            1.0, 1.0, 1.0, 1.0, 0.0, 0.0,
        ),
        EnsembleComplementarityEvidence(),
    )
    assert isinstance(intent.solo_method, SoloDevelopmentOperation)
    assert f"solo_method:{intent.solo_method.value}" in intent.to_soft_plan().candidate_families
