from music_intelligence.harmony.modal_nonfunctional import (
    ContinuityMechanism,
    HarmonicOrientation,
    ModalState,
    NonfunctionalState,
    VerticalTopology,
    assess_modal_state,
    assess_nonfunctional_state,
    modal_characteristic_pc,
)


def test_modal_tonic_bass_strengthens_modal_orientation():
    state = ModalState(
        tonic_pc=2,
        mode_name="D Dorian",
        characteristic_pcs=frozenset({11}),
        current_bass_pc=2,
        observed_pitch_classes=frozenset({2, 5, 9, 11}),
        vertical_topology=VerticalTopology.QUARTAL,
    )
    a = assess_modal_state(state)
    assert a.orientation is HarmonicOrientation.MODAL
    assert a.modal_anchor_strength > .6
    assert ContinuityMechanism.MODAL_TONIC_ANCHOR in a.continuity_mechanisms


def test_same_upper_structure_with_non_tonic_bass_weakens_tonic_perception():
    tonic = assess_modal_state(ModalState(
        tonic_pc=2,
        mode_name="D Dorian",
        current_bass_pc=2,
        vertical_topology=VerticalTopology.QUARTAL,
    ))
    other = assess_modal_state(ModalState(
        tonic_pc=2,
        mode_name="D Dorian",
        current_bass_pc=4,
        vertical_topology=VerticalTopology.QUARTAL,
    ))
    assert tonic.tonic_perception > other.tonic_perception


def test_quartal_topology_has_less_tonal_pull_than_tertian_topology():
    quartal = assess_modal_state(ModalState(
        tonic_pc=2,
        mode_name="D Dorian",
        current_bass_pc=2,
        vertical_topology=VerticalTopology.QUARTAL,
        functional_pull=.4,
    ))
    tertian = assess_modal_state(ModalState(
        tonic_pc=2,
        mode_name="D Dorian",
        current_bass_pc=2,
        vertical_topology=VerticalTopology.TERTIAN,
        functional_pull=.4,
    ))
    assert quartal.tonal_pull_risk < tertian.tonal_pull_risk


def test_characteristic_tone_support_is_explicit():
    b_dorian = modal_characteristic_pc(11, 6, 0)
    state = ModalState(
        tonic_pc=11,
        mode_name="B Dorian",
        characteristic_pcs=frozenset({b_dorian}),
        current_bass_pc=11,
        observed_pitch_classes=frozenset({11, b_dorian}),
    )
    a = assess_modal_state(state)
    assert a.characteristic_tone_support == 1.0
    assert ContinuityMechanism.CHARACTERISTIC_TONE in a.continuity_mechanisms


def test_nonfunctional_coherence_can_come_from_shape_without_tonal_function():
    a = assess_nonfunctional_state(NonfunctionalState(
        continuity_mechanisms=frozenset({ContinuityMechanism.PARALLEL_SHAPE}),
        previous_pitch_classes=frozenset({0, 5, 10}),
        current_pitch_classes=frozenset({2, 7, 0}),
        previous_shape_signature=(5, 5),
        shape_signature=(5, 5),
    ))
    assert a.shape_preserved is True
    assert a.coherence > 0
    assert ContinuityMechanism.INTERVAL_STRUCTURE in a.mechanisms_present


def test_common_tone_and_anchor_can_support_nonfunctional_coherence():
    a = assess_nonfunctional_state(NonfunctionalState(
        continuity_mechanisms=frozenset(),
        structural_anchor_pcs=frozenset({4}),
        previous_pitch_classes=frozenset({0, 4, 7}),
        current_pitch_classes=frozenset({1, 4, 8}),
    ))
    assert a.common_tone_count == 1
    assert a.anchor_count == 1
    assert a.coherence > 0


def test_no_forced_roman_numeral_scale_or_future_voicing():
    state = ModalState(tonic_pc=2, mode_name="D Dorian")
    a = assess_modal_state(state)
    assert not hasattr(a, "roman_numeral")
    assert not hasattr(a, "required_scale")
    assert not hasattr(a, "future_voicing")
