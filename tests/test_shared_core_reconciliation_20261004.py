from music_intelligence.legends.interfaces import (
    VocabularyMemoryItem,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.vocabulary.usage_policy import (
    DIRECT_LITERAL_SHARE,
    choose_runtime_vocabulary_use,
)
from music_intelligence.corpus import (
    coordinate_from_realchord,
    song_from_normalized_record,
)
from music_intelligence.learning import MusicalScoreCoordinate
from music_intelligence.expression import ExpressiveIntent


def _literal_item():
    return VocabularyMemoryItem(
        vocabulary_id="test.literal",
        source_id="test",
        literal_representation="structured_phrase_payload",
        candidate_uses=frozenset({
            VocabularyUseType.LITERAL_QUOTE,
            VocabularyUseType.TRANSPOSED_LICK,
            VocabularyUseType.ADAPTED_LICK,
            VocabularyUseType.FRAGMENT_RECALL,
            VocabularyUseType.ABSTRACTED_PATTERN,
            VocabularyUseType.HYBRID_COMPOSITION,
        }),
    )


def test_literal_vocabulary_runtime_target_is_thirty_percent():
    assert DIRECT_LITERAL_SHARE == .30
    item=_literal_item()
    query=VocabularyQuery(legend_id="shared")
    uses=[
        choose_runtime_vocabulary_use(item,query,opportunity_index=i)
        for i in range(10)
    ]
    assert uses.count(VocabularyUseType.LITERAL_QUOTE)==3


def test_missing_literal_payload_falls_back_to_transformed_use():
    item=VocabularyMemoryItem(
        vocabulary_id="test.abstract",
        source_id="test",
        candidate_uses=frozenset({
            VocabularyUseType.LITERAL_QUOTE,
            VocabularyUseType.ADAPTED_LICK,
            VocabularyUseType.HYBRID_COMPOSITION,
        }),
    )
    use=choose_runtime_vocabulary_use(
        item,VocabularyQuery(legend_id="shared"),opportunity_index=0
    )
    assert use is VocabularyUseType.HYBRID_COMPOSITION


def test_realchord_uses_the_existing_shared_musical_score_coordinate():
    song=song_from_normalized_record({
        "realchord_id":"rc.test",
        "title":"Test",
        "measures":[{
            "measure":1,
            "section":"A",
            "chords":[{"beat":1.0,"symbol":"Cm7"}],
        }],
    })
    pos=coordinate_from_realchord(song,measure=1,beat=1.0)
    assert isinstance(pos,MusicalScoreCoordinate)
    assert pos.realchord_id=="rc.test"


def test_expression_has_one_shared_core_contract():
    intent=ExpressiveIntent()
    intent.validate()
    assert intent.dynamic_level == .5
