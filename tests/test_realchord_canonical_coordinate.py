from music_intelligence.corpus import (
    CanonicalMusicalCoordinate,
    RealChordChordEvent,
    RealChordMeasure,
    RealChordSong,
    expected_harmony_frame,
    parse_realchord_playlist_html,
)
from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonySource,
)


def test_realchord_playlist_ingestion_assigns_stable_source_order_ids():
    html='<a href="irealb://Autumn%20Leaves=Kosma%20Joseph==Medium%20Swing=G-==RAW==0=0===Blue%20Monk=Monk%20Thelonious==Medium%20Swing=Bb==RAW2==0=0">x</a>'
    rows=parse_realchord_playlist_html(html)
    assert rows[0].realchord_id==1
    assert rows[0].title=="Autumn Leaves"
    assert rows[0].key=="G-"
    assert rows[1].realchord_id==2


def test_canonical_coordinate_is_structure_first_not_audio_time():
    c=CanonicalMusicalCoordinate(
        realchord_id=96,
        section="A",
        measure_in_section=1,
        measure_in_form=1,
        beat=0.0,
    )
    c.validate()
    assert not hasattr(c,"onset_sec")
    assert not hasattr(c,"timestamp")


def test_realchord_is_expected_harmony_only():
    song=RealChordSong(
        realchord_id=96,
        title="Autumn Leaves",
        composer="Kosma Joseph",
        style="Medium Swing",
        key="G-",
        measures=(
            RealChordMeasure(
                measure_in_form=1,
                section="A",
                measure_in_section=1,
                chords=(RealChordChordEvent(0.0,"Cm7"),),
            ),
        ),
    )
    coord=CanonicalMusicalCoordinate(96,"A",1,1,0.0)
    observed=HarmonicEvidence(
        source=HarmonySource.OBSERVED,
        symbol="Cm9",
        confidence=.8,
        provenance=("audio_observation",),
    )
    inferred=HarmonicEvidence(
        source=HarmonySource.INFERRED,
        symbol="Cm11",
        confidence=.6,
        provenance=("harmonic_inference",),
    )
    frame=expected_harmony_frame(song,coord,observed=observed,inferred=inferred)
    assert frame.expected.symbol=="Cm7"
    assert frame.observed.symbol=="Cm9"
    assert frame.inferred.symbol=="Cm11"
    assert frame.expected.source is HarmonySource.EXPECTED
