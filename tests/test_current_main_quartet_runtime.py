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



def test_shared_expression_projection_preserves_immediate_event_identity():
    """Shared HOW may alter rendering, never the committed WHAT/event count."""
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

    committed=tuple(
        gesture
        for decision in result.decisions
        for gesture in decision.gestures
    )
    assert len(result.gestures)==len(committed)

    before_pitches=tuple(
        voice.pitch_midi
        for gesture in committed
        for voice in gesture.voices+gesture.drum_hits
    )
    after_pitches=tuple(
        voice.pitch_midi
        for gesture in result.gestures
        for voice in gesture.voices+gesture.drum_hits
    )
    assert after_pitches==before_pitches
    assert len(result.decisions)==len({
        decision.player_id for decision in result.decisions
    })
    assert all(
        gesture.annotations.get("shared_expression")=="canonical"
        for gesture in result.gestures
    )
