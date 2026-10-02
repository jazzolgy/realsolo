from music_intelligence.legends import VocabularyQuery
from music_intelligence.legends.eliot_zigmund import (
    ELIOT_ZIGMUND_PROVISIONAL_VOCABULARY,
    ELIOT_ZIGMUND_VOCABULARY_INDEX,
)


def test_zigmund_runtime_index_is_empty_after_robustness_correction():
    items = ELIOT_ZIGMUND_VOCABULARY_INDEX.query(
        VocabularyQuery(
            legend_id="eliot_zigmund",
            target_instrument="drums",
        )
    )
    assert items == ()


def test_zigmund_provisional_cells_are_preserved_for_research_only():
    assert len(ELIOT_ZIGMUND_PROVISIONAL_VOCABULARY) == 3
    ids = {item.vocabulary_id for item in ELIOT_ZIGMUND_PROVISIONAL_VOCABULARY}
    assert ids == {
        "ez_without_a_song_231",
        "ez_without_a_song_132",
        "ez_without_a_song_312",
    }
    assert all(
        "abstracted_ioi_not_literal_transcription" in item.provenance
        for item in ELIOT_ZIGMUND_PROVISIONAL_VOCABULARY
    )
