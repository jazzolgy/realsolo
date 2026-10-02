import pytest

from music_intelligence.harmony.voice_leading import (
    TargetRole,
    VoiceLeadingContext,
    VoiceRole,
    VoiceState,
    assess_voice_leading,
    make_resolution_debt,
)


def v(voice_id, pitch, role=VoiceRole.GENERIC, harmonic=TargetRole.UNKNOWN):
    return VoiceState(voice_id, pitch, role, harmonic)


def test_common_tone_and_stepwise_motion_are_visible_separately():
    ctx = VoiceLeadingContext(
        current=(v("bass", 48, VoiceRole.BASS), v("top", 64, VoiceRole.TOP)),
        candidate=(v("bass", 48, VoiceRole.BASS), v("top", 65, VoiceRole.TOP)),
    )
    a = assess_voice_leading(ctx)
    assert a.common_tone_count == 1
    assert a.stepwise_count == 1
    assert a.total_motion_semitones == 1


def test_voice_identity_beats_nearest_note_matching_by_default():
    ctx = VoiceLeadingContext(
        current=(v("a", 60), v("b", 72)),
        candidate=(v("a", 71), v("b", 61)),
        preserve_voice_identity=True,
    )
    a = assess_voice_leading(ctx)
    assert {m.from_voice_id + ">" + m.to_voice_id for m in a.motions} == {"a>a", "b>b"}
    assert a.total_motion_semitones == 22


def test_contrary_outer_motion_gets_bonus():
    contrary = assess_voice_leading(VoiceLeadingContext(
        current=(v("bass", 48, VoiceRole.BASS), v("top", 67, VoiceRole.TOP)),
        candidate=(v("bass", 50, VoiceRole.BASS), v("top", 65, VoiceRole.TOP)),
    ))
    similar = assess_voice_leading(VoiceLeadingContext(
        current=(v("bass", 48, VoiceRole.BASS), v("top", 67, VoiceRole.TOP)),
        candidate=(v("bass", 50, VoiceRole.BASS), v("top", 69, VoiceRole.TOP)),
    ))
    assert contrary.contrary_or_oblique_bonus > similar.contrary_or_oblique_bonus


def test_parallel_perfects_are_penalized_but_not_forbidden():
    a = assess_voice_leading(VoiceLeadingContext(
        current=(v("x", 60), v("y", 67)),
        candidate=(v("x", 62), v("y", 69)),
    ))
    assert a.parallel_perfect_penalty > 0
    assert isinstance(a.total_score, float)


def test_guide_tone_target_gets_structural_credit():
    plain = assess_voice_leading(VoiceLeadingContext(
        current=(v("v", 62),),
        candidate=(v("v", 64, harmonic=TargetRole.UNKNOWN),),
    ))
    guide = assess_voice_leading(VoiceLeadingContext(
        current=(v("v", 62),),
        candidate=(v("v", 64, harmonic=TargetRole.GUIDE_TONE),),
    ))
    assert guide.target_arrival_credit > plain.target_arrival_credit


def test_resolution_debt_can_be_paid_by_later_immediate_action():
    debt = make_resolution_debt(
        voice_id="mel",
        source_pitch_midi=68,
        tendency="b9 resolves to root",
        target_pitch_classes=(7,),
        urgency=.9,
    )
    held = assess_voice_leading(VoiceLeadingContext(
        current=(v("mel", 68, VoiceRole.MELODY),),
        candidate=(v("mel", 68, VoiceRole.MELODY),),
        debts=(debt,),
    ))
    resolved = assess_voice_leading(VoiceLeadingContext(
        current=(v("mel", 68, VoiceRole.MELODY),),
        candidate=(v("mel", 67, VoiceRole.MELODY),),
        debts=(debt,),
    ))
    assert held.unresolved_debt_penalty > 0
    assert held.remaining_debts[0].age_events == 1
    assert resolved.debt_resolution_credit > 0
    assert resolved.remaining_debts == ()


def test_target_pitch_class_is_contextual_not_compulsory():
    a = assess_voice_leading(VoiceLeadingContext(
        current=(v("mel", 60),),
        candidate=(v("mel", 62),),
        target_pitch_classes=frozenset({2}),
    ))
    assert a.target_arrival_credit > 0
    assert not hasattr(a, "required_target")


def test_no_future_sequence_or_piano_specific_fields():
    a = assess_voice_leading(VoiceLeadingContext(
        current=(v("x", 60),),
        candidate=(v("x", 61),),
    ))
    assert not hasattr(a, "future_notes")
    assert not hasattr(a, "left_hand")
    assert not hasattr(a, "pedal")
