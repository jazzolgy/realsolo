from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from music_intelligence.reasoning.solo_grammar import SoloDevelopmentOperation
from players.bass import BassMode, BassSequentialRunner, BassStepInput
from players.bass.solo_runtime import (
    BassSoloCandidateFamily,
    BassSoloMemory,
    BassSoloSnapshot,
    choose_bass_solo_plan,
)
from players.bass.solo_method import bass_shared_solo_options
from players.bass.phrase_intent import (
    BassPhraseContext,
    BassPhraseIntent,
    BassPhraseIntentKind,
)


def ev(root, symbol, pcs):
    return HarmonicEvidence(
        source=HarmonySource.EXPECTED,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
    )


def frame():
    return HarmonicFrame(
        expected=ev(2, "Dm7", {2,5,9,0}),
        next_expected=ev(7, "G7", {7,11,2,5}),
    )


def test_solo_mode_exists_and_does_not_default_to_walking_metric_logic():
    runner = BassSequentialRunner()
    result = runner.step(BassStepInput(
        frame=frame(),
        mode=BassMode.SOLO,
        beat_in_measure=0.0,
        absolute_beat=0.0,
        phrase_progress=.45,
        local_key_pitch_classes=frozenset({0,2,4,5,7,9,10}),
    ))
    assert result.candidate.grammar.metric_role.value == "solo_foreground"
    assert result.solo_plan is not None


def test_solo_runtime_bootstraps_material_before_motif_manipulation():
    ctx = BassPhraseContext(phrase_progress=.45, ensemble_activity=.4)
    intent = BassPhraseIntent(BassPhraseIntentKind.DEVELOP)
    options = bass_shared_solo_options(ctx, intent, future_harmony_available=True)
    plan = choose_bass_solo_plan(options, BassSoloSnapshot())
    assert plan.operation in {
        SoloDevelopmentOperation.STATE,
        SoloDevelopmentOperation.TARGET_NEXT_HARMONY,
        SoloDevelopmentOperation.ADD_SPACE,
    }


def test_solo_memory_exposes_committed_motif_intervals():
    mem = BassSoloMemory()
    from music_intelligence.reasoning.legend_style_core import CandidateEvent
    for pitch in (40, 43, 45, 48):
        mem.commit(
            CandidateEvent(pitch, .5, source_family="test"),
            SoloDevelopmentOperation.STATE,
        )
    snap = mem.snapshot()
    assert snap.motif_intervals == (3, 2, 3)


def test_solo_runner_can_use_shorter_than_quarter_note_values():
    runner = BassSequentialRunner()
    durations=[]
    for i, progress in enumerate((.30,.38,.46,.54,.62,.70)):
        out=runner.step(BassStepInput(
            frame=frame(),
            mode=BassMode.SOLO,
            beat_in_measure=(i * .5) % 4,
            absolute_beat=i * .5,
            phrase_progress=progress,
            local_key_pitch_classes=frozenset({0,2,4,5,7,9,10}),
        ))
        durations.append(out.candidate.event.duration_beats)
    assert any(x < 1.0 for x in durations)


def test_solo_source_family_records_method_family():
    runner = BassSequentialRunner()
    out=runner.step(BassStepInput(
        frame=frame(),
        mode=BassMode.SOLO,
        beat_in_measure=1.5,
        absolute_beat=1.5,
        phrase_progress=.65,
        local_key_pitch_classes=frozenset({0,2,4,5,7,9,10}),
    ))
    assert out.candidate.event.source_family.startswith("bass_solo:")
