from music_intelligence.reasoning.intro import (
    EntryAction,
    IntroMode,
    IntroObservation,
    IntroPhase,
    IntroRuntime,
)


def top_mode(result):
    return result.state.mode_hypotheses[0].mode


def test_unknown_is_preserved_when_intro_evidence_is_weak():
    rt = IntroRuntime()
    result = rt.tick(IntroObservation(timestamp=0.0))
    assert result.state.phase is IntroPhase.INTRO_LISTENING
    assert IntroMode.UNKNOWN in {x.mode for x in result.state.mode_hypotheses}
    assert result.decision.action is EntryAction.WAIT


def test_readiness_does_not_equal_permission():
    rt = IntroRuntime()
    result = rt.tick(
        IntroObservation(
            timestamp=0.1,
            rubato_confidence=0.8,
            harmonic_arrival_confidence=1.0,
            expected_head_harmony_match=1.0,
            phrase_boundary_confidence=0.8,
            leader_hold_confidence=0.9,
        )
    )
    assert result.state.entry_readiness > result.state.entry_permission
    assert result.decision.action in {EntryAction.WAIT, EntryAction.SHADOW, EntryAction.LIGHT_SUPPORT}
    assert result.state.phase is not IntroPhase.ENTRY_COMMITTED


def test_rubato_harmonic_arrival_does_not_force_full_join():
    rt = IntroRuntime()
    for i in range(3):
        result = rt.tick(
            IntroObservation(
                timestamp=float(i),
                rubato_confidence=0.95,
                harmonic_arrival_confidence=0.9,
                phrase_boundary_confidence=0.75,
                explicit_entry_cue_confidence=0.45,
                leader_hold_confidence=0.3,
            )
        )
    assert result.state.rubato_probability > 0.5
    assert result.decision.action is not EntryAction.FULL_JOIN


def test_vocal_count_in_can_reach_committed_entry():
    rt = IntroRuntime()
    observations = [
        IntroObservation(
            timestamp=0.0,
            vocal_count_confidence=0.95,
            iois_seconds=(0.5, 0.5, 0.5),
            meter_hint=(4, 4),
            beat_phase_hint=0.0,
            phrase_boundary_confidence=0.7,
            explicit_entry_cue_confidence=0.8,
        ),
        IntroObservation(
            timestamp=0.5,
            vocal_count_confidence=1.0,
            iois_seconds=(0.5, 0.5, 0.5),
            meter_hint=(4, 4),
            beat_phase_hint=0.0,
            phrase_boundary_confidence=1.0,
            explicit_entry_cue_confidence=1.0,
            expected_head_harmony_match=0.9,
        ),
        IntroObservation(
            timestamp=1.0,
            vocal_count_confidence=1.0,
            iois_seconds=(0.5, 0.5, 0.5),
            meter_hint=(4, 4),
            beat_phase_hint=0.0,
            phrase_boundary_confidence=1.0,
            explicit_entry_cue_confidence=1.0,
            expected_head_harmony_match=1.0,
        ),
        IntroObservation(
            timestamp=1.5,
            vocal_count_confidence=1.0,
            iois_seconds=(0.5, 0.5, 0.5),
            meter_hint=(4, 4),
            beat_phase_hint=0.0,
            phrase_boundary_confidence=1.0,
            explicit_entry_cue_confidence=1.0,
            expected_head_harmony_match=1.0,
        ),
    ]
    for obs in observations:
        result = rt.tick(obs)

    assert result.state.tempo_estimate_bpm is not None
    assert 115.0 <= result.state.tempo_estimate_bpm <= 125.0
    assert result.state.entry_permission > 0.7
    assert result.decision.action in {EntryAction.PARTIAL_JOIN, EntryAction.FULL_JOIN}


def test_pickup_sets_downbeat_target_without_precomposed_phrase():
    rt = IntroRuntime()
    result = rt.tick(
        IntroObservation(
            timestamp=0.0,
            pickup_confidence=0.95,
            iois_seconds=(0.25, 0.25),
            beat_phase_hint=None,
            explicit_entry_cue_confidence=0.8,
            phrase_boundary_confidence=0.9,
            expected_head_harmony_match=0.9,
        )
    )
    assert result.state.entry_target_beat_phase == 0.0
    assert not hasattr(result.decision, "future_notes")
    assert not hasattr(result.decision, "phrase_sequence")


def test_committed_entry_handoffs_to_normal_runtime():
    rt = IntroRuntime()
    for i in range(6):
        result = rt.tick(
            IntroObservation(
                timestamp=i * 0.5,
                direct_head_confidence=1.0,
                iois_seconds=(0.5, 0.5, 0.5),
                beat_phase_hint=0.0,
                meter_hint=(4, 4),
                explicit_entry_cue_confidence=1.0,
                phrase_boundary_confidence=1.0,
                expected_head_harmony_match=1.0,
            )
        )
        if result.state.phase is IntroPhase.ENTRY_COMMITTED:
            break

    assert result.state.phase is IntroPhase.ENTRY_COMMITTED
    state = rt.handoff_to_normal_runtime()
    assert state.phase is IntroPhase.NORMAL_ENSEMBLE_RUNTIME
