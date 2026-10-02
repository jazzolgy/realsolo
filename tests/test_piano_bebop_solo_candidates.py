from players.piano import (
    BebopDensityDirection,
    BebopEntryMode,
    BebopPhraseIntent,
    BebopTargetMode,
    ResolvedHarmonicMaterial,
    generate_immediate_bebop_candidates,
)


def current_material():
    return ResolvedHarmonicMaterial(
        affordance_id="current",
        root_pitch_class=7,
        role_pitch_classes={
            "root": (7,),
            "3rd": (11,),
            "b7": (5,),
            "9": (9,),
        },
    )


def next_material():
    return ResolvedHarmonicMaterial(
        affordance_id="next",
        root_pitch_class=0,
        role_pitch_classes={
            "root": (0,),
            "3rd": (4,),
            "7th": (11,),
        },
    )


def intent(
    entry=BebopEntryMode.CONTINUE,
    target=BebopTargetMode.GUIDE_TONE,
    families=("close_approach","passing","neighbor"),
    density=BebopDensityDirection.STABLE,
):
    return BebopPhraseIntent(
        horizon_beats=2.0,
        entry_mode=entry,
        target_mode=target,
        density_direction=density,
        connector_families=families,
        confidence=0.8,
    )


def test_generator_produces_current_harmony_targets_and_connectors():
    candidates=generate_immediate_bebop_candidates(
        current_material=current_material(),
        intent=intent(),
        previous_pitch_midi=67,
        low_midi=60,
        high_midi=84,
    )
    assert any("guide_tone" in c.tags for c in candidates if c.pitch_midi is not None)
    assert any("close_approach" in c.tags for c in candidates)
    assert any("neighbor" in c.tags for c in candidates)
    assert any("passing" in c.tags for c in candidates)


def test_next_harmony_intent_uses_next_material_and_anticipation_tags():
    candidates=generate_immediate_bebop_candidates(
        current_material=current_material(),
        next_material=next_material(),
        intent=intent(
            entry=BebopEntryMode.PICKUP,
            target=BebopTargetMode.NEXT_HARMONY,
            families=("anticipation","close_approach"),
        ),
        previous_pitch_midi=69,
        low_midi=60,
        high_midi=84,
    )
    structural=[
        c for c in candidates
        if c.pitch_midi is not None and "next_harmony_target" in c.tags
    ]
    assert structural
    assert all(c.onset_offset_beats < 0 for c in structural)
    assert all("anticipation" in c.tags for c in structural)


def test_resolution_intent_marks_structural_targets_as_directed():
    candidates=generate_immediate_bebop_candidates(
        current_material=current_material(),
        intent=intent(
            target=BebopTargetMode.RESOLUTION,
            families=("close_approach",),
        ),
        low_midi=60,
        high_midi=84,
    )
    structural=[
        c for c in candidates
        if c.pitch_midi is not None and "chord_tone" in c.tags
    ]
    assert structural
    assert all("directed_target" in c.tags for c in structural)
    assert all("resolution_path" in c.tags for c in structural)


def test_hold_space_intent_includes_rest_without_removing_note_choices():
    candidates=generate_immediate_bebop_candidates(
        current_material=current_material(),
        intent=intent(
            entry=BebopEntryMode.HOLD_SPACE,
            target=BebopTargetMode.OPEN,
            families=("passing",),
            density=BebopDensityDirection.RELEASE,
        ),
        previous_pitch_midi=67,
    )
    assert any(c.pitch_midi is None for c in candidates)
    assert any(c.pitch_midi is not None for c in candidates)


def test_generator_returns_only_immediate_events_not_future_phrase_objects():
    candidates=generate_immediate_bebop_candidates(
        current_material=current_material(),
        intent=intent(),
        previous_pitch_midi=67,
    )
    assert candidates
    assert all(not hasattr(c,"future_notes") for c in candidates)
    assert all(not hasattr(c,"next_events") for c in candidates)
    assert all(not hasattr(c,"phrase_sequence") for c in candidates)
