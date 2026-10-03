from music_intelligence.corpus import (
    RealChordChord,
    RealChordMeasure,
    RealChordSong,
    find_realchord_song,
    parse_realchord_playlist_html,
)
from music_intelligence.learning import PerformancePhase
from music_intelligence.research.harmony_expression import (
    build_harmony_conditioned_expression,
    same_expected_harmony_context,
)


def test_playlist_ingestion_preserves_source_order_and_raw_chart():
    html=(
        '<a href="irealb://'
        'Blue%20Monk=Monk%20Thelonious==Medium%20Swing=Bb==RAW1==0=0==='
        'Autumn%20Leaves=Kosma%20Joseph==Medium%20Swing=G-==RAW2==0=0'
        '">x</a>'
    )
    rows=parse_realchord_playlist_html(html)
    autumn=find_realchord_song(rows,"Autumn Leaves")
    assert autumn.realchord_id=="2"
    assert autumn.source_index==2
    assert autumn.key=="G-"
    assert autumn.style=="Medium Swing"
    assert autumn.raw_chart=="RAW2"


def _song():
    return RealChordSong(
        realchord_id="96",
        title="Autumn Leaves",
        style="Medium Swing",
        key="G-",
        form="32-bar",
        measures=(
            RealChordMeasure(
                measure=1,
                section="A1",
                chords=(RealChordChord(beat=1.0,symbol="Cm7"),),
            ),
            RealChordMeasure(
                measure=2,
                section="A1",
                chords=(RealChordChord(beat=1.0,symbol="F7"),),
            ),
        ),
        provenance=("realchord:1350","source_index:96"),
    )


def test_same_expected_harmony_can_have_different_expression_by_phase():
    song=_song()
    head=build_harmony_conditioned_expression(
        observation_id="head-1",
        song=song,measure=1,beat=1.0,chorus_index=0,
        performance_phase=PerformancePhase.HEAD,
        dynamic_proxy=.42,accent_proxy=.70,
    )
    solo=build_harmony_conditioned_expression(
        observation_id="solo-1",
        song=song,measure=1,beat=1.0,chorus_index=2,
        performance_phase=PerformancePhase.SOLO,
        dynamic_proxy=.68,accent_proxy=.52,
    )
    assert same_expected_harmony_context(head,solo,require_same_form_bar=True)
    assert head.dynamic_proxy != solo.dynamic_proxy
    assert head.coordinate.chord_label=="Cm7"
    assert solo.coordinate.realchord_id=="96"
