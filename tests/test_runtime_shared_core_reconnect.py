from realtime.ensemble_app.shared_core_runtime import build_shared_core_runtime_tick
from music_intelligence.corpus.realchord import (
    RealChordChord,
    RealChordMeasure,
    RealChordSong,
)
from music_intelligence.learning.score_alignment import PerformancePhase


def _song():
    return RealChordSong(
        realchord_id="rc:test",
        title="Test Tune",
        form="AB",
        measures=(
            RealChordMeasure(
                measure=1,
                section="A",
                chords=(RealChordChord(beat=1.0,symbol="Dm7"),),
            ),
            RealChordMeasure(
                measure=2,
                section="A",
                chords=(RealChordChord(beat=1.0,symbol="G7"),),
            ),
        ),
        provenance=("realchord:test",),
    )


def test_runtime_tick_uses_realchord_for_canonical_position_and_expected_harmony():
    tick=build_shared_core_runtime_tick(
        song_id="ignored",
        section="",
        bar_index=0,
        beat_in_bar=0.0,
        total_bars=2,
        chorus_index=3,
        performance_phase=PerformancePhase.SOLO,
        phrase_maturity=.4,
        tension=.6,
        ensemble_density=.5,
        realchord_song=_song(),
    )
    assert tick.position.realchord_id=="rc:test"
    assert tick.position.bar==1
    assert tick.position.chorus_index==3
    assert tick.expected_harmony is not None
    assert tick.expected_harmony.chord_symbol=="Dm7"
    assert set(tick.expressive_intents)=={"sax","piano","bass","drums"}


def test_runtime_chart_fallback_still_uses_musical_score_coordinate():
    tick=build_shared_core_runtime_tick(
        song_id="Runtime Tune",
        section="B",
        bar_index=7,
        beat_in_bar=2.0,
        total_bars=32,
        chorus_index=1,
        performance_phase=PerformancePhase.SOLO,
        phrase_maturity=.8,
        tension=.7,
        ensemble_density=.6,
    )
    assert tick.position.song_id=="Runtime Tune"
    assert tick.position.form_bar==8
    assert tick.position.section=="B"
    assert tick.expected_harmony is None
