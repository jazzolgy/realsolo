from music_intelligence.corpus import (
    CorpusRegistry,
    CorpusUse,
    ExpectedHarmonyReference,
    REALCHORD_1350_DATASET_ID,
    coordinate_from_realchord,
    expected_harmony_at,
    register_realchord_1350,
    song_from_normalized_record,
)


def sample_song():
    return song_from_normalized_record({
        "realchord_id": "rc.autumn_leaves",
        "title": "Autumn Leaves",
        "composer": "Joseph Kosma",
        "style": "swing",
        "key": "G minor",
        "form": "AABC",
        "provenance": ["fixture:realchord"],
        "measures": [
            {
                "measure": 1,
                "section": "A1",
                "chords": [
                    {"beat": 1.0, "symbol": "Cm7"},
                    {"beat": 3.0, "symbol": "F7"},
                ],
            },
            {
                "measure": 2,
                "section": "A1",
                "chords": [{"beat": 1.0, "symbol": "Bbmaj7"}],
                "repeat_start": True,
            },
        ],
    })


def test_realchord_1350_is_one_shared_symbolic_corpus_item():
    registry=CorpusRegistry()
    register_realchord_1350(registry)
    item=registry.get(REALCHORD_1350_DATASET_ID)
    assert "shared_core" in item.tags
    assert "expected_harmony" in item.tags
    assert CorpusUse.RESEARCH in item.uses
    assert CorpusUse.TRAINING not in item.uses


def test_normalized_record_preserves_form_section_repeat_and_chords():
    song=sample_song()
    assert song.realchord_id=="rc.autumn_leaves"
    assert song.form=="AABC"
    assert song.measure_at(1).section=="A1"
    assert song.measure_at(2).repeat_start is True
    assert [x.symbol for x in song.measure_at(1).chords]==["Cm7","F7"]


def test_expected_harmony_is_reference_not_performance_claim():
    song=sample_song()
    first=expected_harmony_at(song,measure=1,beat=1.5)
    later=expected_harmony_at(song,measure=1,beat=3.5)
    assert isinstance(first,ExpectedHarmonyReference)
    assert first.chord_symbol=="Cm7"
    assert later.chord_symbol=="F7"


def test_realchord_coordinate_becomes_canonical_bar_beat_reference():
    song=sample_song()
    pos=coordinate_from_realchord(song,measure=1,beat=3.5,chorus_index=2)
    pos.validate()
    assert pos.realchord_id=="rc.autumn_leaves"
    assert pos.score_source_id=="realchord:rc.autumn_leaves"
    assert pos.section=="A1"
    assert pos.bar==1
    assert pos.beat==3.5
    assert pos.form_bar==1
    assert pos.chorus_index==2
    assert pos.chord_label=="F7"
    assert pos.within_core_form is True


def test_realchord_identity_requires_an_explicit_score_source():
    from music_intelligence.learning import MusicalScoreCoordinate
    import pytest

    pos=MusicalScoreCoordinate(song_id="x",realchord_id="rc.x")
    with pytest.raises(ValueError,match="score_source_id"):
        pos.validate()
