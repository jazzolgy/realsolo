from music_intelligence.legends import VocabularyUseType
from music_intelligence.legends.eliot_zigmund import ELIOT_ZIGMUND_PROVISIONAL_VOCABULARY
from music_intelligence.reasoning.motif import MotifIdentity, motif_identity_from_vocabulary
from players.drums.legend_adapter import drum_vocabulary_intent
from players.drums.model import DrummerRuntimeContext
from players.drums.solo import DrumSoloPlan, DrumSoloState, SoloDevelopment, build_solo_candidates


def provisional_item():
    return next(
        item for item in ELIOT_ZIGMUND_PROVISIONAL_VOCABULARY
        if item.vocabulary_id == "ez_without_a_song_231"
    )


def test_provisional_item_can_still_be_inspected_through_shared_motif_bridge():
    item = provisional_item()
    shared = motif_identity_from_vocabulary(item)
    assert isinstance(shared, MotifIdentity)
    assert shared.rhythm_schema == (2.0, 3.0, 1.0)
    assert shared.accent_shape == (0.638, 0.720, 0.613, 0.659)
    assert "shared_motif:vocabulary_bridge" in shared.provenance


def test_manual_research_injection_uses_shared_path_without_making_it_runtime_active():
    item = provisional_item()
    intent = drum_vocabulary_intent(
        item,
        use_type=VocabularyUseType.ABSTRACTED_PATTERN,
    )
    assert intent.shared_motif_identity is not None

    candidates = build_solo_candidates(
        DrumSoloPlan(),
        DrummerRuntimeContext(position_in_bar_beats=0.0),
        DrumSoloState(),
        vocabulary_intents=(intent,),
    )
    state = next(c for c in candidates if c.development is SoloDevelopment.STATE)
    assert state.motif_identity is not None
    assert state.motif_identity.source == "shared_motif_identity"
    assert state.motif_identity.onset_units == (0, 2, 5, 6)
    assert "players_drums:rhythmic_projection" in state.motif_identity.provenance
