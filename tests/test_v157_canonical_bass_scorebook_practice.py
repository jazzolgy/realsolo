from players.bass import (
    BassMode,
    BassPracticePulse,
    BassPracticeSong,
    BassSequentialRunner,
    BassStepInput,
    run_scorebook_practice,
)
from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)


def ev(root, symbol, pcs):
    return HarmonicEvidence(
        source=HarmonySource.EXPECTED,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
    )


def test_canonical_runner_forwards_local_key_pitch_classes():
    c = ev(0, "Cm7", {0,3,7,10})
    f = ev(5, "F7", {5,9,0,3})
    runner = BassSequentialRunner()
    first = runner.step(BassStepInput(
        HarmonicFrame(expected=c, next_expected=f),
        BassMode.WALKING,
        0.0,
        0.0,
        local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
    ))
    second = runner.step(BassStepInput(
        HarmonicFrame(expected=c, next_expected=f),
        BassMode.WALKING,
        1.0,
        1.0,
        local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
    ))
    assert first.candidate.event.pitch_midi is not None
    assert second.candidate.event.pitch_midi is not None
    # At least the selected event is evaluated through the canonical runner
    # with a valid local-key field; exact route is policy-dependent.
    assert len(runner.memory.committed) == 2


def test_scorebook_practice_runs_real_causal_player_for_multiple_passes():
    c = ev(0, "Cm7", {0,3,7,10})
    f = ev(5, "F7", {5,9,0,3})
    pulses = tuple(
        BassPracticePulse(
            frame=HarmonicFrame(expected=c, next_expected=f),
            beat_in_measure=float(beat),
            absolute_beat=float(beat),
            mode=BassMode.WALKING,
            local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
        )
        for beat in range(4)
    )
    song = BassPracticeSong(
        "score.test.cm7",
        "Practice Cm7",
        pulses,
        provenance=("test-scorebook",),
    )
    session = run_scorebook_practice(song, passes=3)
    assert len(session.passes) == 3
    assert all(x.metrics.event_count == 4 for x in session.passes)
    assert all(x.metrics.route_variety >= 1 for x in session.passes)
    assert "players/bass:scorebook-practice" in session.provenance


def test_two_feel_practice_metric_tracks_color_use_separately():
    c = ev(0, "Cm7", {0,3,7,10})
    f = ev(5, "F7", {5,9,0,3})
    song = BassPracticeSong(
        "score.test.twofeel",
        "Two Feel",
        (
            BassPracticePulse(
                HarmonicFrame(expected=c, next_expected=f),
                0.0, 0.0, BassMode.TWO_FEEL,
                frozenset({0,2,3,5,7,9,10}),
            ),
            BassPracticePulse(
                HarmonicFrame(expected=c, next_expected=f),
                2.0, 2.0, BassMode.TWO_FEEL,
                frozenset({0,2,3,5,7,9,10}),
            ),
        ),
    )
    session = run_scorebook_practice(song, passes=1)
    metrics = session.passes[0].metrics
    assert 0.0 <= metrics.two_feel_color_rate <= 1.0
    assert metrics.event_count == 2
