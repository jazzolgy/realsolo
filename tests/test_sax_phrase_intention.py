from music_intelligence.harmony.scale_linear_core import LinearRouteKind
from players.sax.phrase_intention import (
    SaxPhraseIntentionMemory,
    choose_sax_phrase_intention,
)
from realtime.ensemble_app.canonical_repertoire import AUTUMN_LEAVES_G_MINOR_JAM
from realtime.ensemble_app.quartet_rehearsal import run_quartet_song_chart
from realtime.ensemble_app.stage1_quartet import Stage1QuartetRuntime


def test_develop_phase_prefers_linear_bebop_routes_over_plain_chordal():
    d=choose_sax_phrase_intention(
        phrase_maturity=.42,
        beat_in_bar=1.5,
        section="A",
        tension=.55,
        previous_pitch_midi=67,
        recent_event_count=3,
    )
    assert d.phase=="develop"
    assert d.route_biases[LinearRouteKind.APPROACH] > d.route_biases[LinearRouteKind.CHORDAL]
    assert d.route_biases[LinearRouteKind.ENCLOSURE] > d.route_biases[LinearRouteKind.CHORDAL]
    assert d.route_biases[LinearRouteKind.CHROMATIC_PASSING] > d.route_biases[LinearRouteKind.CHORDAL]


def test_release_phase_creates_longer_occupancy_and_space_pressure():
    d=choose_sax_phrase_intention(
        phrase_maturity=.94,
        beat_in_bar=1.0,
        section="A",
        tension=.28,
        previous_pitch_midi=70,
        recent_event_count=7,
    )
    assert d.phase=="release"
    assert d.duration_beats >= 1.0
    assert d.rest_bias >= .2
    assert d.register_direction == -1


def test_duration_memory_holds_future_ticks_without_precomposed_pitch():
    memory=SaxPhraseIntentionMemory()
    memory.commit_duration(1.5,decision_step_beats=.5)
    assert memory.held_ticks_remaining==2
    assert memory.consume_hold()
    assert memory.consume_hold()
    assert not memory.consume_hold()
    assert not hasattr(memory,"future_pitches")
    assert not hasattr(memory,"future_notes")


def test_autumn_leaves_quartet_emits_multiple_sax_phrase_intention_phases():
    chart=AUTUMN_LEAVES_G_MINOR_JAM
    quartet=Stage1QuartetRuntime.create(chart.tempo_bpm)
    log=run_quartet_song_chart(quartet,chart,subdivisions_per_beat=2)

    phases=set()
    sax_durations=set()
    sax_space_ticks=0
    for tick in log.ticks:
        sax_intents=[x for x in tick.intents if x["player_id"]=="sax"]
        if sax_intents and sax_intents[0]["density"]==0:
            sax_space_ticks += 1
        for gesture in tick.gestures:
            if gesture.get("source")!="player/sax:canonical_immediate":
                continue
            phase=gesture.get("annotations",{}).get("phrase_intention")
            if phase:
                phases.add(phase)
            for voice in gesture.get("voices",()):
                sax_durations.add(float(voice["duration_beats"]))

    assert {"attack","develop","target","release"}.issubset(phases)
    assert any(x > .5 for x in sax_durations)
    assert sax_space_ticks > 0
