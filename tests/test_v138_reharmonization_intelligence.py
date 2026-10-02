from music_intelligence.harmony.reharmonization import (
    ContinuityAxis,
    HarmonicSnapshot,
    ReharmonizationKind,
    ReharmonizationProposal,
    assess_reharmonization,
    make_substitute_dominant_proposal,
    tritone_substitute_root,
)


def test_tritone_substitute_root_is_six_semitones_away():
    assert tritone_substitute_root(7) == 1
    assert tritone_substitute_root(0) == 6


def test_substitute_dominant_can_preserve_target_and_function():
    p = make_substitute_dominant_proposal(
        proposal_id="g7_to_db7",
        dominant_root_pc=7,
        target_root_pc=0,
        original_pitch_classes=(7, 11, 2, 5),
        substitute_pitch_classes=(1, 5, 8, 11),
        melody_pcs=(11,),
    )
    a = assess_reharmonization(p)
    assert a.target_preservation >= .9
    assert a.function_preservation > .8
    assert ContinuityAxis.TARGET_PRESERVATION in a.accepted_axes


def test_reharmonization_is_not_accepted_by_kind_alone():
    p = ReharmonizationProposal(
        proposal_id="weak_sub",
        kind=ReharmonizationKind.SUBSTITUTE_DOMINANT,
        original=HarmonicSnapshot(
            root_pc=7,
            pitch_classes=frozenset({7, 11, 2, 5}),
            function="dominant",
            target_root_pc=0,
            melody_pcs=frozenset({4}),
        ),
        substitute=HarmonicSnapshot(
            root_pc=3,
            pitch_classes=frozenset({3, 6, 10}),
            function="color",
            target_root_pc=8,
            melody_pcs=frozenset({4}),
        ),
        intended_target_pc=0,
    )
    a = assess_reharmonization(p)
    assert a.risk > 0
    assert a.target_preservation < 1


def test_common_tone_and_melody_compatibility_raise_continuity():
    good = ReharmonizationProposal(
        proposal_id="good",
        kind=ReharmonizationKind.INTERPOLATION,
        original=HarmonicSnapshot(
            root_pc=0,
            pitch_classes=frozenset({0, 4, 7, 11}),
            melody_pcs=frozenset({4}),
        ),
        substitute=HarmonicSnapshot(
            root_pc=4,
            pitch_classes=frozenset({4, 7, 11, 2}),
            melody_pcs=frozenset({4}),
        ),
    )
    weak = ReharmonizationProposal(
        proposal_id="weak",
        kind=ReharmonizationKind.INTERPOLATION,
        original=good.original,
        substitute=HarmonicSnapshot(
            root_pc=1,
            pitch_classes=frozenset({1, 6, 10}),
            melody_pcs=frozenset({4}),
        ),
    )
    assert assess_reharmonization(good).continuity_score > assess_reharmonization(weak).continuity_score


def test_modal_interchange_is_a_relation_not_a_forced_scale():
    p = ReharmonizationProposal(
        proposal_id="borrow",
        kind=ReharmonizationKind.MODAL_INTERCHANGE,
        original=HarmonicSnapshot(
            root_pc=0,
            pitch_classes=frozenset({0, 4, 7, 11}),
            key_context="C major",
        ),
        substitute=HarmonicSnapshot(
            root_pc=0,
            pitch_classes=frozenset({0, 3, 7, 10}),
            key_context="C parallel minor",
        ),
    )
    a = assess_reharmonization(p)
    assert a.modal_borrowing_support > 0
    assert not hasattr(a, "required_scale")


def test_reharmonization_carries_no_fixed_future_sequence():
    p = ReharmonizationProposal(
        proposal_id="x",
        kind=ReharmonizationKind.CHROMATIC_APPROACH,
        original=HarmonicSnapshot(root_pc=0),
        substitute=HarmonicSnapshot(root_pc=1),
    )
    assert not hasattr(p, "future_chords")
    assert not hasattr(p, "future_notes")
    assert not hasattr(p, "voicing_pitches")
