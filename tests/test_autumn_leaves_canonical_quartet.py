from realtime.ensemble_app.canonical_repertoire import AUTUMN_LEAVES_G_MINOR_JAM
from realtime.ensemble_app.quartet_rehearsal import run_quartet_song_chart
from realtime.ensemble_app.stage1_quartet import Stage1QuartetRuntime


def test_autumn_leaves_fixture_is_one_32_bar_g_minor_jam_form():
    chart=AUTUMN_LEAVES_G_MINOR_JAM
    assert len(chart.bars)==32
    assert chart.tempo_bpm==172.0
    assert chart.bars[0].chords==("Cm7",)
    assert chart.bars[5].chords==("D7",)
    assert chart.bars[6].chords==("Gm",)
    assert chart.bars[26].chords==("Gm","C7")
    assert chart.bars[29].chords==("Am7b5","D7")


def test_autumn_leaves_canonical_quartet_runs_one_causal_form():
    chart=AUTUMN_LEAVES_G_MINOR_JAM
    quartet=Stage1QuartetRuntime.create(chart.tempo_bpm)
    log=run_quartet_song_chart(quartet,chart,subdivisions_per_beat=1)

    assert len(log.ticks)==32*4
    assert {x.bar_index for x in log.ticks}==set(range(32))

    for tick in log.ticks:
        assert {x["player_id"] for x in tick.directives}=={
            "piano","bass","drums","sax"
        }
        assert {x["player_id"] for x in tick.intents}=={
            "piano","bass","drums","sax"
        }
        assert all(
            "performance_convention:jazz_jam_session" in x["tags"]
            for x in tick.directives
        )
        assert tick.published_generation>tick.snapshot_generation

    generations=[x.snapshot_generation for x in log.ticks]
    assert generations==sorted(generations)
    assert all(b>a for a,b in zip(generations,generations[1:]))


def test_autumn_leaves_e2e_reaches_portable_renderer_packets():
    chart=AUTUMN_LEAVES_G_MINOR_JAM
    quartet=Stage1QuartetRuntime.create(chart.tempo_bpm)
    log=run_quartet_song_chart(quartet,chart,subdivisions_per_beat=1)

    packets=[
        packet
        for tick in log.ticks
        for packet in tick.portable_packets
    ]
    assert packets
    assert all(packet["protocol_version"]==1 for packet in packets)
    roles={
        voice["instrument_role"]
        for packet in packets
        for voice in (
            packet["gesture"]["voices"]
            + packet["gesture"]["drum_hits"]
        )
    }
    assert {"piano","bass","drums","tenor_sax"}.issubset(roles)


def test_half_bar_changes_are_seen_at_the_correct_runtime_ticks():
    chart=AUTUMN_LEAVES_G_MINOR_JAM
    quartet=Stage1QuartetRuntime.create(chart.tempo_bpm)
    log=run_quartet_song_chart(quartet,chart,subdivisions_per_beat=1)

    bar26=[x for x in log.ticks if x.bar_index==26]
    assert [x.chord_symbol for x in bar26]==["Gm","Gm","C7","C7"]

    bar29=[x for x in log.ticks if x.bar_index==29]
    assert [x.chord_symbol for x in bar29]==["Am7b5","Am7b5","D7","D7"]


def test_first_canonical_pass_is_elastic_with_human_drift_off():
    chart=AUTUMN_LEAVES_G_MINOR_JAM
    quartet=Stage1QuartetRuntime.create(chart.tempo_bpm)
    assert quartet.state.groove.coordination_mode.value=="elastic"
    assert quartet.state.groove.tempo_elasticity==0.0
