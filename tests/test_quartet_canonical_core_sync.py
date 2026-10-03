from music_intelligence.corpus import song_from_normalized_record
from music_intelligence.expression import ExpressiveIntent
from music_intelligence.learning import MusicalScoreCoordinate
from realtime.ensemble_app.stage1_quartet import Stage1QuartetRuntime


def _song():
    return song_from_normalized_record({
        "realchord_id":"rc.autumn_leaves.test",
        "title":"Autumn Leaves",
        "style":"swing",
        "key":"G minor",
        "form":"32bar",
        "measures":[
            {
                "measure":1,
                "section":"A",
                "chords":[{"beat":1.0,"symbol":"Cm7"}],
            },
            {
                "measure":2,
                "section":"A",
                "chords":[{"beat":1.0,"symbol":"F7"}],
            },
        ],
    })


def test_quartet_accepts_shared_realchord_without_replacing_audio_truth():
    runtime=Stage1QuartetRuntime.create(172.0)
    runtime.attach_realchord_song(_song())
    assert runtime.realchord_song.realchord_id=="rc.autumn_leaves.test"


def test_quartet_emits_shared_expression_controls_for_playing_roles():
    runtime=Stage1QuartetRuntime.create(172.0)
    runtime.attach_realchord_song(_song())
    result=runtime.decide(
        "Cm7","F7",
        beat_in_bar=0.0,
        bar_index=0,
        total_bars=32,
        tempo_bpm=172.0,
        section="A",
        chorus=0,
    )
    voices=[
        voice
        for gesture in result.gestures
        for voice in (gesture.voices+gesture.drum_hits)
    ]
    assert voices
    controlled=[v for v in voices if v.expression_controls]
    assert controlled
    for voice in controlled:
        assert "dynamic_level" in voice.expression_controls
        assert "accent_strength" in voice.expression_controls
        assert "foreground_weight" in voice.expression_controls


def test_realchord_and_shared_how_use_shared_core_types():
    runtime=Stage1QuartetRuntime.create(172.0)
    runtime.attach_realchord_song(_song())
    coord=MusicalScoreCoordinate(
        song_id="Autumn Leaves",
        score_source_id="realchord:rc.autumn_leaves.test",
        realchord_id="rc.autumn_leaves.test",
        section="A",
        bar=1,
        beat=1.0,
    )
    coord.validate()
    intent=ExpressiveIntent()
    intent.validate()
