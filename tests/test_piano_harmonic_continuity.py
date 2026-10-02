from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from music_intelligence.reasoning.online_improviser import SoftPlan
from players.piano import (
    CompingActionType,
    HarmonicContinuityMemory,
    InteractionRole,
    PianoCompingCandidate,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    estimate_harmonic_continuity,
    perform_one_comping_action,
)


def frame(symbol, root, *, phrase=0.2, cadence="open", next_symbol=None, next_root=None):
    expected = HarmonicEvidence(
        HarmonySource.EXPECTED,
        symbol=symbol,
        root_pc=root,
    )
    next_expected = None
    if next_symbol is not None:
        next_expected = HarmonicEvidence(
            HarmonySource.EXPECTED,
            symbol=next_symbol,
            root_pc=next_root,
        )
    return HarmonicFrame(
        expected=expected,
        next_expected=next_expected,
        phrase_position=phrase,
        cadence_state=cadence,
    )


def test_static_harmony_builds_high_hold_stability():
    memory = HarmonicContinuityMemory()
    features = None
    for _ in range(5):
        features = memory.observe(frame("Dm7", 2))
    assert features is not None
    assert features.hold_stability > 0.8
    assert features.pattern_consistency_strength > 0.6


def test_repeating_two_chord_vamp_keeps_high_recurrence_despite_high_change_rate():
    memory = HarmonicContinuityMemory()
    sequence = [("Gm7", 7), ("C7", 0), ("Gm7", 7), ("C7", 0), ("Gm7", 7), ("C7", 0)]
    features = None
    for symbol, root in sequence:
        features = memory.observe(frame(symbol, root))
    assert features is not None
    assert features.change_rate > 0.8
    assert features.recurrence_strength >= 0.8
    assert features.pattern_consistency_strength > 0.5


def test_nonrecurring_fast_harmony_has_lower_consistency_than_repeating_vamp():
    vamp = HarmonicContinuityMemory()
    for symbol, root in [("Gm7",7),("C7",0),("Gm7",7),("C7",0),("Gm7",7),("C7",0)]:
        vamp_features = vamp.observe(frame(symbol, root))

    moving = HarmonicContinuityMemory()
    for symbol, root in [("Dm7",2),("G7",7),("Cmaj7",0),("Fmaj7",5),("Bm7b5",11),("E7",4)]:
        moving_features = moving.observe(frame(symbol, root))

    assert moving_features.change_rate > 0.8
    assert moving_features.recurrence_strength < vamp_features.recurrence_strength
    assert moving_features.pattern_consistency_strength < vamp_features.pattern_consistency_strength


def test_phrase_boundary_lowers_pattern_consistency():
    memory = HarmonicContinuityMemory()
    for _ in range(4):
        memory.observe(frame("Dm7", 2, phrase=0.3))

    middle = estimate_harmonic_continuity(
        frame("Dm7", 2, phrase=0.4),
        memory.history,
    )
    boundary = estimate_harmonic_continuity(
        frame("Dm7", 2, phrase=0.98, cadence="cadential"),
        memory.history,
    )
    assert boundary.boundary_pressure > middle.boundary_pressure
    assert boundary.pattern_consistency_strength < middle.pattern_consistency_strength


def test_known_imminent_harmony_change_adds_boundary_pressure():
    memory = HarmonicContinuityMemory()
    for _ in range(3):
        memory.observe(frame("Dm7", 2))

    stable = estimate_harmonic_continuity(
        frame("Dm7", 2, next_symbol="Dm7", next_root=2),
        memory.history,
    )
    changing = estimate_harmonic_continuity(
        frame("Dm7", 2, next_symbol="G7", next_root=7),
        memory.history,
    )
    assert changing.boundary_pressure > stable.boundary_pressure


def test_manual_pattern_consistency_remains_available_for_ablation():
    state = PianoCompingState()
    context = PianoCompingContext(
        pattern_consistency_strength=0.73,
        auto_pattern_consistency=False,
    )
    state.observe_harmonic_frame(frame("Dm7", 2))
    assert state.effective_pattern_consistency(context) == 0.73


def test_auto_pattern_consistency_uses_latest_harmonic_features():
    state = PianoCompingState()
    context = PianoCompingContext(
        pattern_consistency_strength=0.0,
        auto_pattern_consistency=True,
    )
    for _ in range(4):
        features = state.observe_harmonic_frame(frame("Dm7", 2))
    assert state.effective_pattern_consistency(context) == features.pattern_consistency_strength
    assert state.effective_pattern_consistency(context) > 0.5


def test_runtime_observes_harmonic_frame_before_immediate_choice():
    state = PianoCompingState()
    context = PianoCompingContext()
    silence = PianoCompingCandidate(
        action_type=CompingActionType.SILENCE,
        role=InteractionRole.LAY_OUT,
        duration_beats=0.5,
    )

    perform_one_comping_action(
        SoftPlan(1, "yield"),
        PianoCompingEvaluator(),
        (silence,),
        context,
        MusicalContextVector(),
        state,
        harmonic_frame=frame("Dm7", 2),
    )

    assert state.last_harmonic_continuity is not None
    assert len(state.harmonic_continuity.history) == 1
    assert len(state.committed) == 1


def test_harmonic_continuity_memory_contains_no_future_gesture_plan():
    memory = HarmonicContinuityMemory()
    memory.observe(frame("Gm7", 7, next_symbol="C7", next_root=0))
    assert not hasattr(memory, "future_actions")
    assert not hasattr(memory, "future_voicings")
    assert not hasattr(memory, "future_pattern")
