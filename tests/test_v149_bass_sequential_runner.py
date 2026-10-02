from music_intelligence.bass import (
    BassMode,
    BassSequentialRunner,
    BassStepInput,
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


def test_runner_commits_each_action_before_next_decision():
    c = ev(0, "Cm7", {0,3,7,10})
    f = ev(5, "F7", {5,9,0,3})
    runner = BassSequentialRunner(tempo_bpm=120.0)
    steps = (
        BassStepInput(HarmonicFrame(expected=c, next_expected=f), BassMode.WALKING, 0.0, 0.0),
        BassStepInput(HarmonicFrame(expected=c, next_expected=f), BassMode.WALKING, 1.0, 1.0),
        BassStepInput(HarmonicFrame(expected=c, next_expected=f), BassMode.WALKING, 2.0, 2.0),
        BassStepInput(HarmonicFrame(expected=c, next_expected=f), BassMode.WALKING, 3.0, 3.0),
    )
    result = runner.run(steps)
    assert len(result) == 4
    assert len(runner.memory.committed) == 4
    assert result[-1].candidate.event.pitch_midi == runner.memory.committed[-1].event.pitch_midi


def test_runner_preserves_two_feel_as_two_committed_actions_when_caller_schedules_two():
    c = ev(0, "Cm7", {0,3,7,10})
    f = ev(5, "F7", {5,9,0,3})
    runner = BassSequentialRunner()
    result = runner.run((
        BassStepInput(HarmonicFrame(expected=c, next_expected=f), BassMode.TWO_FEEL, 0.0, 0.0),
        BassStepInput(HarmonicFrame(expected=c, next_expected=f), BassMode.TWO_FEEL, 2.0, 2.0),
    ))
    assert len(result) == 2
    assert all(x.candidate.event.duration_beats == 2.0 for x in result)
