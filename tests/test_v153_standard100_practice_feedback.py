from music_intelligence.bass import (
    BassContext,
    BassMode,
    BassPerformanceMemory,
    BassCommittedAction,
    generate_immediate_bass_candidates,
)
from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from music_intelligence.reasoning.legend_style_core import CandidateEvent


def ev(root, symbol, pcs):
    return HarmonicEvidence(
        source=HarmonySource.EXPECTED,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
    )


def commit(memory, pitch, role):
    memory.commit(BassCommittedAction(
        CandidateEvent(pitch_midi=pitch, duration_beats=1.0, source_family="test"),
        harmonic_role=role,
        metric_role="continuation",
    ))


def test_recent_approach_budget_penalizes_another_directed_target():
    memory = BassPerformanceMemory()
    for pitch, role in (
        (40, "root"),
        (42, "chord_tone"),
        (41, "chromatic_approach"),
        (43, "root"),
        (45, "chord_tone"),
        (44, "anticipation"),
        (43, "root"),
        (42, "chord_tone"),
    ):
        commit(memory, pitch, role)
    snap = memory.snapshot()
    frame = HarmonicFrame(
        expected=ev(0, "Cm7", {0,3,7,10}),
        next_expected=ev(5, "F7", {5,9,0,3}),
    )
    items = generate_immediate_bass_candidates(
        frame,
        BassContext(
            mode=BassMode.WALKING,
            beat_in_measure=3.0,
            previous_pitch_midi=42,
            memory_snapshot=snap,
        ),
    )
    directed = [x for x in items if x.harmonic_role.value in {"chromatic_approach","anticipation"}]
    assert directed
    assert any("recent approach budget already used" in x.reasons for x in directed)


def test_soft_contour_fatigue_appears_after_two_same_direction_moves():
    memory = BassPerformanceMemory()
    for pitch in (36, 40, 43):
        commit(memory, pitch, "chord_tone")
    snap = memory.snapshot()
    frame = HarmonicFrame(expected=ev(0, "Cm7", {0,3,7,10}))
    items = generate_immediate_bass_candidates(
        frame,
        BassContext(
            mode=BassMode.WALKING,
            beat_in_measure=1.0,
            previous_pitch_midi=43,
            previous_motion_semitones=3,
            memory_snapshot=snap,
        ),
    )
    assert any("soft contour-fatigue pressure" in x.reasons for x in items)
