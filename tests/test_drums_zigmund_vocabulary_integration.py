from music_intelligence.legends import (
    VocabularyDimension,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.legends.eliot_zigmund import ELIOT_ZIGMUND_VOCABULARY_INDEX
from players.drums.legend_adapter import drum_vocabulary_intent
from players.drums.model import DrummerRuntimeContext
from players.drums.solo import (
    DrumSoloPlan,
    DrumSoloState,
    SoloDevelopment,
    build_solo_candidates,
)


def test_zigmund_provider_returns_source_grounded_drum_cells():
    items = ELIOT_ZIGMUND_VOCABULARY_INDEX.query(
        VocabularyQuery(
            legend_id="eliot_zigmund",
            context_tags=frozenset({"drum_solo", "triplet_grid"}),
            required_dimensions=frozenset({VocabularyDimension.RHYTHM}),
            target_instrument="drums",
        )
    )
    assert len(items) == 3
    assert all(item.source_instrument == "drums" for item in items)
    assert all("without_a_song" in item.tune_id for item in items)


def test_zigmund_231_cell_becomes_actual_solo_motif_seed():
    item = next(
        item for item in ELIOT_ZIGMUND_VOCABULARY_INDEX.items
        if item.vocabulary_id == "ez_without_a_song_231"
    )
    intent = drum_vocabulary_intent(
        item,
        use_type=VocabularyUseType.ABSTRACTED_PATTERN,
    )
    plan = DrumSoloPlan()
    state = DrumSoloState()
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0)

    candidates = build_solo_candidates(
        plan,
        ctx,
        state,
        vocabulary_intents=(intent,),
    )
    state_candidate = next(
        candidate for candidate in candidates
        if candidate.development is SoloDevelopment.STATE
    )

    motif = state_candidate.motif_identity
    assert motif is not None
    assert motif.onset_units == (0, 2, 5, 6)
    assert motif.accent_vector == (0.638, 0.720, 0.613, 0.659)
    assert motif.source == "shared_legend_vocabulary:bill_evans_without_a_song_1977"
    assert len(state_candidate.gesture.hits) <= 1


def test_legend_memory_changes_seed_without_freezing_future_phrase():
    item = ELIOT_ZIGMUND_VOCABULARY_INDEX.items[0]
    intent = drum_vocabulary_intent(
        item,
        use_type=VocabularyUseType.HYBRID_COMPOSITION,
    )
    state = DrumSoloState()
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0)
    candidates = build_solo_candidates(
        DrumSoloPlan(),
        ctx,
        state,
        vocabulary_intents=(intent,),
    )
    assert any(
        c.motif_identity is not None
        and c.motif_identity.source.startswith("shared_legend_vocabulary:")
        for c in candidates
        if c.development is not SoloDevelopment.ADD_SPACE
    )
    assert not hasattr(state, "future_phrase")
