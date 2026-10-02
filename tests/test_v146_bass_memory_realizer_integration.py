from music_intelligence.bass import (
    BassContext,
    BassInteractionContext,
    BassMode,
    BassPerformanceMemory,
    BassCommittedAction,
    choose_bass_interaction_intent,
    generate_immediate_bass_candidates,
)
from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from music_intelligence.reasoning.legend_style_core import CandidateEvent


def ev(source, root, symbol, pcs):
    return HarmonicEvidence(
        source=source,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
    )


def test_stepwise_saturation_reduces_another_step():
    memory = BassPerformanceMemory()
    for p in (40, 42, 44, 45):
        memory.commit(BassCommittedAction(CandidateEvent(
            pitch_midi=p,
            duration_beats=1.0,
            source_family="test",
        )))
    snap = memory.snapshot()

    frame = HarmonicFrame(
        expected=ev(HarmonySource.EXPECTED, 10, "Bbmaj7", {10, 2, 5, 9}),
    )
    items = generate_immediate_bass_candidates(
        frame,
        BassContext(
            mode=BassMode.WALKING,
            beat_in_measure=1.0,
            previous_pitch_midi=45,
            memory_snapshot=snap,
        ),
    )
    assert any("stepwise momentum saturation" in x.reasons for x in items)


def test_register_recovery_rewards_opposite_direction():
    memory = BassPerformanceMemory()
    for p in (36, 40, 43, 47):
        memory.commit(BassCommittedAction(CandidateEvent(
            pitch_midi=p,
            duration_beats=1.0,
            source_family="test",
        )))
    snap = memory.snapshot()
    decision = choose_bass_interaction_intent(
        BassInteractionContext(memory=snap)
    )

    frame = HarmonicFrame(
        expected=ev(HarmonySource.EXPECTED, 0, "Cm7", {0, 3, 7, 10}),
    )
    items = generate_immediate_bass_candidates(
        frame,
        BassContext(
            mode=BassMode.WALKING,
            beat_in_measure=1.0,
            previous_pitch_midi=47,
            memory_snapshot=snap,
            interaction_decision=decision,
        ),
    )
    assert any("supports register recovery" in x.reasons for x in items)
    assert any("extends register excursion" in x.reasons for x in items)
