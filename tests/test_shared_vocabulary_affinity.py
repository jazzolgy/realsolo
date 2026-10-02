from music_intelligence.legends import (
    VocabularyDimension,
    VocabularyMemoryItem,
    VocabularyQuery,
)
from music_intelligence.vocabulary import (
    dimension_affinity,
    rank_vocabulary_items,
    score_vocabulary_item,
    source_instrument_affinity,
)


def item(
    vocabulary_id,
    source_instrument,
    *,
    confidence=.9,
    dimensions=frozenset({VocabularyDimension.RHYTHM}),
    harmony_context="",
    recent_usage_count=0,
):
    return VocabularyMemoryItem(
        vocabulary_id=vocabulary_id,
        source_id="test",
        source_instrument=source_instrument,
        dimensions=dimensions,
        transferable_to=frozenset({"piano","sax","bass","drums"}),
        confidence=confidence,
        harmony_context=harmony_context,
        recent_usage_count=recent_usage_count,
    )


def test_same_instrument_is_soft_preference():
    sax=item("SAX","sax",confidence=.90)
    piano=item("PIANO","piano",confidence=.90)
    ranked=rank_vocabulary_items(
        (piano,sax),
        VocabularyQuery(
            legend_id="charlie_parker",
            target_instrument="sax",
            required_dimensions=frozenset({VocabularyDimension.RHYTHM}),
        ),
    )
    assert ranked[0].vocabulary_id=="SAX"
    assert source_instrument_affinity("sax","sax") > source_instrument_affinity("piano","sax")


def test_context_fit_can_override_same_instrument_bias():
    same=item("SAME","sax",confidence=.84,harmony_context="minor")
    cross=item("CROSS","piano",confidence=.90,harmony_context="dominant")
    ranked=rank_vocabulary_items(
        (same,cross),
        VocabularyQuery(
            legend_id="charlie_parker",
            target_instrument="sax",
            required_dimensions=frozenset({VocabularyDimension.RHYTHM}),
            harmony_context="dominant",
        ),
    )
    assert ranked[0].vocabulary_id=="CROSS"


def test_drum_rhythm_transfers_but_pitch_has_no_special_drum_affinity():
    rhythm=dimension_affinity(
        "drums","piano",frozenset({VocabularyDimension.RHYTHM})
    )
    pitch=dimension_affinity(
        "drums","piano",frozenset({VocabularyDimension.PITCH_INTERVAL})
    )
    assert rhythm > 0
    assert pitch == 0


def test_recent_use_can_outweigh_affinity():
    repeated=item("REPEATED","sax",confidence=.9,recent_usage_count=6)
    fresh=item("FRESH","piano",confidence=.9,recent_usage_count=0)
    ranked=rank_vocabulary_items(
        (repeated,fresh),
        VocabularyQuery(
            legend_id="charlie_parker",
            target_instrument="sax",
            required_dimensions=frozenset({VocabularyDimension.RHYTHM}),
        ),
    )
    assert ranked[0].vocabulary_id=="FRESH"


def test_breakdown_exposes_affinity_components():
    x=item(
        "X","drums",
        dimensions=frozenset({
            VocabularyDimension.RHYTHM,
            VocabularyDimension.ACCENT,
        }),
    )
    score=score_vocabulary_item(
        x,
        VocabularyQuery(
            legend_id="charlie_parker",
            target_instrument="piano",
            required_dimensions=frozenset({VocabularyDimension.RHYTHM}),
        ),
    )
    assert score is not None
    assert score.instrument_affinity == 0
    assert score.dimension_affinity > 0
