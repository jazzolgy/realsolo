import pytest

from players.piano import (
    EnergyDirection,
    PhraseSpaceWindow,
    PianoDensity,
    PianoInteractionState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    generate_minimal_voicing_families,
    generate_rootless_voicings,
    generate_shell_voicings,
)


def dominant_material():
    return ResolvedHarmonicMaterial(
        affordance_id="dominant.altered_color",
        root_pitch_class=7,
        role_pitch_classes={
            "root": (7,),
            "3rd": (11,),
            "b7": (5,),
            "b9": (8,),
            "#9": (10,),
            "b13": (3,),
        },
    )


def test_density_is_multidimensional_and_validated():
    low = PianoDensity(voice_count=2, onset_rate=0.5, dynamic_weight=0.3)
    high = PianoDensity(
        voice_count=5,
        onset_rate=3.0,
        sustain_ratio=0.8,
        register_span=30,
        registral_concentration=0.8,
        dynamic_weight=0.9,
        pedal_blur=0.7,
    )
    assert low.intrusion_index < high.intrusion_index


def test_phrase_space_is_an_opportunity_not_future_notes():
    window = PhraseSpaceWindow(
        confidence=0.9,
        start_offset_beats=0.25,
        estimated_length_beats=1.0,
        source="solo_phrase_boundary",
    )
    assert window.usable is True
    assert not hasattr(window, "notes")


def test_interaction_state_accepts_energy_direction():
    state = PianoInteractionState(
        soloist_activity=0.2,
        phrase_space=PhraseSpaceWindow(0.8, estimated_length_beats=1.0),
        energy_direction=EnergyDirection.UP,
    )
    state.validate()
    assert state.phrase_space.usable


def test_shell_generator_uses_resolved_roles_without_parsing_chord_symbol():
    request = PianoVoicingRequest(
        material=dominant_material(),
        bassist_present=True,
    )
    candidates = generate_shell_voicings(request)
    assert candidates
    for candidate in candidates:
        roles = {v.harmonic_role for v in candidate.event.voices}
        assert {"3rd", "7th"}.issubset(roles)
        assert "root" not in roles
        assert candidate.event.annotations["harmonic_affordance_id"] == "dominant.altered_color"


def test_shell_can_include_root_when_bassist_is_absent():
    request = PianoVoicingRequest(
        material=dominant_material(),
        bassist_present=False,
    )
    candidate = generate_shell_voicings(request)[0]
    roles = {v.harmonic_role for v in candidate.event.voices}
    assert "root" in roles


def test_rootless_generator_exposes_multiple_color_candidates():
    request = PianoVoicingRequest(
        material=dominant_material(),
        bassist_present=True,
    )
    candidates = generate_rootless_voicings(request)
    assert len(candidates) >= 3
    colors = {
        role
        for candidate in candidates
        for role in (v.harmonic_role for v in candidate.event.voices)
        if role not in {"3rd", "7th"}
    }
    assert {"b9", "#9", "b13"}.issubset(colors)


def test_voicing_generator_has_no_chord_symbol_api():
    request = PianoVoicingRequest(material=dominant_material())
    assert not hasattr(request, "chord_symbol")
    assert not hasattr(request.material, "symbol")


def test_missing_guide_tone_roles_yields_no_shell_instead_of_guessing_harmony():
    material = ResolvedHarmonicMaterial(
        affordance_id="unknown.color",
        role_pitch_classes={"root": (0,), "9th": (2,)},
    )
    assert generate_shell_voicings(PianoVoicingRequest(material)) == ()


def test_minimal_family_generator_returns_shell_and_rootless_candidates():
    candidates = generate_minimal_voicing_families(
        PianoVoicingRequest(dominant_material())
    )
    families = {candidate.event.source_family for candidate in candidates}
    assert "piano_shell" in families
    assert "piano_rootless" in families


def test_out_of_range_request_is_rejected():
    with pytest.raises(ValueError):
        generate_shell_voicings(
            PianoVoicingRequest(
                dominant_material(),
                low_midi=10,
            )
        )
