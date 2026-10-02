from music_intelligence.legends import (
    LegendDomain,
    VocabularyDimension,
    VocabularyMemoryItem,
    VocabularyUseType,
)
from music_intelligence.reasoning.motif import motif_identity_from_vocabulary


def test_shared_vocabulary_becomes_shared_motif_identity():
    item = VocabularyMemoryItem(
        vocabulary_id="test_231",
        source_id="recording_x",
        transposition_normalized_representation=(
            "ioi:2,3,1|accent:0.6,0.8,0.5,0.7"
        ),
        rhythm="triplet_grid_ioi_2_3_1",
        contour="four_event_cell",
        source_instrument="drums",
        dimensions=frozenset({
            VocabularyDimension.RHYTHM,
            VocabularyDimension.ACCENT,
        }),
        domains=frozenset({LegendDomain.RHYTHM_SUBDIVISION}),
        candidate_uses=frozenset({VocabularyUseType.ABSTRACTED_PATTERN}),
    )
    motif = motif_identity_from_vocabulary(item)
    assert motif is not None
    assert motif.rhythm_schema == (2.0, 3.0, 1.0)
    assert motif.accent_shape == (0.6, 0.8, 0.5, 0.7)
    assert motif.event_count_hint == 4
    assert motif.interaction_function == "vocabulary_recall"
    assert not hasattr(motif, "future_notes")


def test_shared_vocabulary_bridge_rejects_unparseable_ioi():
    item = VocabularyMemoryItem(
        vocabulary_id="bad",
        source_id="source",
        transposition_normalized_representation="ioi:x,3,1",
        candidate_uses=frozenset({VocabularyUseType.ABSTRACTED_PATTERN}),
    )
    assert motif_identity_from_vocabulary(item) is None
