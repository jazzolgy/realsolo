from music_intelligence.transcribe.allocation import (
    AllocationEvidence,
    StaffProfile,
    allocation_candidates,
    preferred_allocation,
)


PIANO_STAFFS = (
    StaffProfile(
        "piano:upper",
        "piano",
        role_tags=frozenset({"melody", "upper", "inner_voice"}),
        nominal_low_midi=55,
        nominal_high_midi=108,
    ),
    StaffProfile(
        "piano:lower",
        "piano",
        role_tags=frozenset({"bass", "lower"}),
        nominal_low_midi=21,
        nominal_high_midi=72,
    ),
)


def test_role_and_register_can_rank_staff_without_hard_coding_piano_policy():
    evidence = AllocationEvidence(
        source_event_ids=("piano:1",),
        nominal_midi=43,
        voice_role="bass",
    )
    best = preferred_allocation(evidence, PIANO_STAFFS)
    assert best.staff_id == "piano:lower"


def test_explicit_context_can_override_generic_register_hint():
    evidence = AllocationEvidence(
        source_event_ids=("piano:2",),
        nominal_midi=60,
        voice_role="inner_voice",
        preferred_staff_id="piano:lower",
    )
    best = preferred_allocation(evidence, PIANO_STAFFS)
    assert best.staff_id == "piano:lower"
    assert "explicit notation-context staff preference" in best.reasons


def test_allocation_keeps_alternative_staff_hypotheses():
    evidence = AllocationEvidence(
        source_event_ids=("piano:3",),
        nominal_midi=60,
    )
    candidates = allocation_candidates(evidence, PIANO_STAFFS)
    assert {c.staff_id for c in candidates} == {"piano:upper", "piano:lower"}


def test_voice_staff_is_not_conflated_with_player_or_instrument_identity():
    evidence = AllocationEvidence(
        source_event_ids=("sax:1",),
        nominal_midi=67,
        voice_role="melody",
    )
    staffs = (
        StaffProfile(
            "score:tenor-sax",
            "part:tenor-sax",
            role_tags=frozenset({"melody"}),
            nominal_low_midi=48,
            nominal_high_midi=90,
        ),
    )
    result = preferred_allocation(evidence, staffs)
    assert result.staff_id == "score:tenor-sax"
    assert result.voice_id != "sax"
    assert result.voice_id != "tenor_sax"
