from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from players.piano import (
    BebopDensityDirection,
    BebopEntryMode,
    BebopHarmonicPhase,
    BebopHarmonicTurnContext,
    BebopTargetMode,
    BebopTurnTakingEvidence,
    BebopTurnTakingType,
    EnsembleBreathType,
    EnsembleComplementarityEvidence,
    derive_bebop_phrase_intent,
)


def harmonic_turn(phase):
    return BebopHarmonicTurnContext(
        phase=phase,
        turn_type=BebopTurnTakingType.AMBIGUOUS,
        phrase_boundary_pressure=0.8 if phase is BebopHarmonicPhase.FORM_BOUNDARY else 0.1,
        anticipation_strength=0.8 if phase is BebopHarmonicPhase.ANTICIPATORY else 0.1,
        resolution_strength=0.8 if phase is BebopHarmonicPhase.DIRECTED_RESOLUTION else 0.1,
        stability_strength=0.8 if phase is BebopHarmonicPhase.STABLE_FIELD else 0.1,
        confidence=0.9,
    )


def turn(kind=BebopTurnTakingType.AMBIGUOUS):
    return BebopTurnTakingEvidence(
        kind,
        0.3,
        0.7,
        0.7,
        3.0,
        0.8,
        0.0,
    )


def complementarity(kind=EnsembleBreathType.NONE, low=0.4, perc=0.4):
    return EnsembleComplementarityEvidence(
        breath_type=kind,
        foreground_drop=0.6,
        low_harmonic_support=low,
        percussive_support=perc,
        post_foreground_reentry=0.5,
        confidence=0.8,
    )


def test_anticipatory_intent_uses_pickup_and_next_harmony_target():
    intent=derive_bebop_phrase_intent(
        harmonic_turn(BebopHarmonicPhase.ANTICIPATORY),
        turn(),
        complementarity(),
    )
    assert intent.entry_mode is BebopEntryMode.PICKUP
    assert intent.target_mode is BebopTargetMode.NEXT_HARMONY
    assert "anticipation" in intent.connector_families


def test_directed_resolution_intent_preserves_resolution_path():
    intent=derive_bebop_phrase_intent(
        harmonic_turn(BebopHarmonicPhase.DIRECTED_RESOLUTION),
        turn(),
        complementarity(),
    )
    assert intent.target_mode is BebopTargetMode.RESOLUTION
    assert "resolution_path" in intent.connector_families


def test_stable_field_allows_longer_color_development():
    intent=derive_bebop_phrase_intent(
        harmonic_turn(BebopHarmonicPhase.STABLE_FIELD),
        turn(),
        complementarity(),
    )
    assert intent.target_mode is BebopTargetMode.COLOR
    assert intent.horizon_beats >= 3.0
    assert "motif_continuation" in intent.connector_families


def test_form_boundary_opens_new_phrase_intent():
    intent=derive_bebop_phrase_intent(
        harmonic_turn(BebopHarmonicPhase.FORM_BOUNDARY),
        turn(),
        complementarity(),
    )
    assert intent.entry_mode is BebopEntryMode.NEW_PHRASE
    assert intent.density_direction is BebopDensityDirection.RELEASE


def test_supported_handoff_reentry_overrides_redundant_new_entry():
    intent=derive_bebop_phrase_intent(
        harmonic_turn(BebopHarmonicPhase.FORM_BOUNDARY),
        turn(BebopTurnTakingType.SUPPORTED_HANDOFF_REENTRY),
        complementarity(),
    )
    assert intent.entry_mode is BebopEntryMode.CONTINUE


def test_unresolved_collective_release_can_hold_space():
    intent=derive_bebop_phrase_intent(
        harmonic_turn(BebopHarmonicPhase.STABLE_FIELD),
        turn(BebopTurnTakingType.AMBIGUOUS),
        complementarity(EnsembleBreathType.COLLECTIVE_RELEASE,low=0.2,perc=0.2),
    )
    assert intent.entry_mode is BebopEntryMode.HOLD_SPACE
    assert intent.target_mode is BebopTargetMode.OPEN


def test_active_supported_handoff_redirects_density_sparse():
    intent=derive_bebop_phrase_intent(
        harmonic_turn(BebopHarmonicPhase.STABLE_FIELD),
        turn(),
        complementarity(EnsembleBreathType.FOREGROUND_HANDOFF,low=0.9,perc=0.8),
    )
    assert intent.density_direction is BebopDensityDirection.SPARSE


def test_soft_plan_contains_no_exact_future_notes():
    intent=derive_bebop_phrase_intent(
        harmonic_turn(BebopHarmonicPhase.DIRECTED_RESOLUTION),
        turn(),
        complementarity(),
    )
    plan=intent.to_soft_plan()
    plan.validate_for_improvisation()
    assert plan.exact_future_notes == ()
    assert not hasattr(intent,"exact_future_notes")
