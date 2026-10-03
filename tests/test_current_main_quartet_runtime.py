from realtime.ensemble_app.stage1_quartet import Stage1QuartetRuntime

from music_intelligence.corpus.realchord import (
    RealChordChord,
    RealChordMeasure,
    RealChordSong,
)


def _autumn_leaves_reference() -> RealChordSong:
    return RealChordSong(
        realchord_id="autumn-leaves",
        title="Autumn Leaves",
        key="G-",
        form="32-bar",
        measures=tuple(
            RealChordMeasure(
                measure=i,
                section=(
                    "A1" if i <= 8
                    else "A2" if i <= 16
                    else "B" if i <= 24
                    else "C"
                ),
                chords=(RealChordChord(beat=0.0, symbol="Cm7" if i == 1 else "F7"),),
            )
            for i in range(1,33)
        ),
        provenance=("test:normalized_realchord",),
    )


def test_current_main_quartet_runtime_consumes_canonical_shared_context():
    runtime=Stage1QuartetRuntime.create(172.0)
    runtime.realchord_song=_autumn_leaves_reference()
    result=runtime.decide(
        "Cm7",
        "F7",
        beat_in_bar=0.0,
        bar_index=0,
        total_bars=32,
        tempo_bpm=172.0,
        section="A1",
        chorus=0,
    )
    assert result.state.transport.bar == 0
    assert result.state.transport.section == "A1"
    assert result.gestures
