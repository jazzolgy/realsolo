import pytest

from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
    HarmonicIntent,
    affordance_ids,
    build_basic_affordances,
)


def evidence(source, symbol=None, function=None, root=0):
    return HarmonicEvidence(source=source, symbol=symbol, function=function, root_pc=root)


def test_expected_observed_inferred_are_not_collapsed():
    frame = HarmonicFrame(
        expected=evidence(HarmonySource.EXPECTED, "G7", "dominant", 7),
        observed=HarmonicEvidence(
            source=HarmonySource.OBSERVED,
            pitch_classes=frozenset({7, 11, 2, 5, 8}),
            confidence=.8,
        ),
        inferred=evidence(HarmonySource.INFERRED, "G7alt", "dominant", 7),
    )
    frame.validate()
    assert frame.expected.symbol == "G7"
    assert frame.observed.symbol is None
    assert frame.inferred.symbol == "G7alt"


def test_wrong_evidence_slot_is_rejected():
    frame = HarmonicFrame(
        expected=evidence(HarmonySource.INFERRED, "G7", "dominant", 7),
    )
    with pytest.raises(ValueError):
        frame.validate()


def test_dominant_exposes_multiple_affordances_not_one_scale():
    frame = HarmonicFrame(
        expected=evidence(HarmonySource.EXPECTED, "G7", "dominant", 7),
        next_expected=evidence(HarmonySource.EXPECTED, "Cmaj7", "tonic_major", 0),
        tension=.72,
    )
    items = build_basic_affordances(frame)
    ids = affordance_ids(items)
    assert "dominant.stable_identity" in ids
    assert "dominant.altered_color" in ids
    assert "future_harmony.anticipation" in ids
    assert "outside.return_path" in ids
    assert not any(hasattr(x, "required_scale") for x in items)


def test_altered_dominant_supports_chained_colors_with_resolution_path():
    frame = HarmonicFrame(expected=evidence(HarmonySource.EXPECTED, "G7", "dominant", 7))
    alt = next(x for x in build_basic_affordances(frame) if x.affordance_id == "dominant.altered_color")
    assert {x.label for x in alt.tension_choices} == {"b9", "#9", "b13"}
    assert "directed_resolution" in alt.continuity_mechanisms


def test_major7_natural_11_is_contextual_not_absolute_ban():
    frame = HarmonicFrame(expected=evidence(HarmonySource.EXPECTED, "Cmaj7", "tonic_major", 0))
    color = next(x for x in build_basic_affordances(frame) if x.affordance_id == "major7.color_field")
    natural_11 = next(x for x in color.tension_choices if x.label == "11")
    assert natural_11.exposed_weight < 0
    assert natural_11.requires_resolution is True


def test_minor_harmony_does_not_force_dorian_or_aeolian():
    frame = HarmonicFrame(expected=evidence(HarmonySource.EXPECTED, "Fm7", "minor", 5))
    items = build_basic_affordances(frame)
    minor = next(x for x in items if x.affordance_id == "minor.contextual_color")
    assert minor.intent is HarmonicIntent.COLOR
    assert "modal_context" in minor.continuity_mechanisms
    assert not any("dorian" in x.note.lower() or "aeolian" in x.note.lower() for x in items)


def test_affordances_contain_roles_and_routes_not_exact_future_notes():
    frame = HarmonicFrame(
        expected=evidence(HarmonySource.EXPECTED, "G7", "dominant", 7),
        next_expected=evidence(HarmonySource.EXPECTED, "Cmaj7", "tonic_major", 0),
    )
    for item in build_basic_affordances(frame):
        assert not hasattr(item, "exact_future_notes")
        assert not hasattr(item, "voicing_pitches")
