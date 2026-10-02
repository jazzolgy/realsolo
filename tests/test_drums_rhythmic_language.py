from players.drums.model import DrummerRuntimeContext, DrumVoice, GestureRole
from players.drums.rhythmic_language import (
    RhythmicTransform,
    engineering_seed_motif,
    realize_motif_now,
    transform_motif,
)


def test_repeat_preserves_actual_rhythmic_identity():
    motif = engineering_seed_motif()
    repeated = transform_motif(motif, RhythmicTransform.REPEAT)
    assert repeated.onset_units == motif.onset_units
    assert repeated.iois == motif.iois
    assert repeated.accent_vector == motif.accent_vector


def test_displace_moves_actual_onsets_not_just_a_tag():
    motif = engineering_seed_motif()
    displaced = transform_motif(motif, RhythmicTransform.DISPLACE, amount_units=2)
    assert displaced.onset_units != motif.onset_units
    assert sorted(displaced.iois) == sorted(motif.iois)


def test_reorchestrate_preserves_rhythm_but_changes_kit_contour():
    motif = engineering_seed_motif()
    orch = transform_motif(motif, RhythmicTransform.REORCHESTRATE)
    assert orch.onset_units == motif.onset_units
    assert orch.orchestration_contour != motif.orchestration_contour


def test_internal_rest_removes_a_real_onset():
    motif = engineering_seed_motif()
    rested = transform_motif(motif, RhythmicTransform.INTERNAL_REST)
    assert len(rested.onset_units) == len(motif.onset_units) - 1


def test_hybrid_keeps_identity_and_adds_new_material():
    motif = engineering_seed_motif()
    hybrid = transform_motif(motif, RhythmicTransform.HYBRIDIZE)
    assert set(motif.onset_units).issubset(set(hybrid.onset_units))
    assert len(hybrid.onset_units) == len(motif.onset_units) + 1


def test_runtime_realizes_only_current_event_not_future_phrase():
    motif = engineering_seed_motif()
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.0, beats_per_bar=4)
    gesture = realize_motif_now(
        motif, ctx, intensity=0.6, development_tag="state"
    )
    assert gesture.role is GestureRole.FILL
    assert len(gesture.hits) == 1
    assert not hasattr(gesture, "future_hits")


def test_runtime_can_return_space_between_motif_onsets():
    motif = engineering_seed_motif()
    ctx = DrummerRuntimeContext(position_in_bar_beats=0.5, beats_per_bar=4)
    gesture = realize_motif_now(
        motif, ctx, intensity=0.6, development_tag="repeat"
    )
    assert gesture.role is GestureRole.SPACE
    assert not gesture.hits
