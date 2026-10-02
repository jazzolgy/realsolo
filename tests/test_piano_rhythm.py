import pytest

from music_intelligence.reasoning.polyphonic_event import PolyphonicEventCandidate, VoiceEvent
from players.piano import (
    CompingActionType,
    InteractionRole,
    PianoCompingCandidate,
    PianoRealizationCandidate,
    RhythmicPlacement,
    apply_rhythmic_intent,
    expand_rhythmic_variants,
    rhythmic_intents_for_candidate,
)


def candidate(
    *,
    action=CompingActionType.PUNCTUATION,
    role=InteractionRole.PUNCTUATE,
    duration=0.5,
):
    event = PolyphonicEventCandidate(
        voices=(
            VoiceEvent("low", 52, onset_offset_beats=-0.01),
            VoiceEvent("top", 64, onset_offset_beats=0.02),
        ),
        duration_beats=duration,
        role="comping",
    )
    return PianoCompingCandidate(
        action_type=action,
        role=role,
        duration_beats=duration,
        realization=PianoRealizationCandidate(event),
    )


def test_punctuation_exposes_onbeat_anticipated_and_offbeat_options():
    intents = rhythmic_intents_for_candidate(
        candidate(),
        phrase_boundary_probability=0.4,
        available_space_beats=0.0,
        drummer_activity=0.8,
    )
    placements = {x.placement for x in intents}
    assert RhythmicPlacement.ON_BEAT in placements
    assert RhythmicPlacement.ANTICIPATED in placements
    assert RhythmicPlacement.OFFBEAT in placements


def test_answer_gets_delayed_option_when_phrase_space_is_available():
    c = candidate(
        action=CompingActionType.RESPONSE,
        role=InteractionRole.ANSWER,
    )
    intents = rhythmic_intents_for_candidate(
        c,
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        drummer_activity=0.4,
    )
    assert RhythmicPlacement.DELAYED in {x.placement for x in intents}


def test_no_delayed_answer_without_reliable_phrase_space():
    c = candidate(
        action=CompingActionType.RESPONSE,
        role=InteractionRole.ANSWER,
    )
    intents = rhythmic_intents_for_candidate(
        c,
        phrase_boundary_probability=0.2,
        available_space_beats=0.0,
        drummer_activity=0.4,
    )
    assert RhythmicPlacement.DELAYED not in {x.placement for x in intents}


def test_rhythmic_intent_moves_group_anchor_but_preserves_internal_spread():
    c = candidate()
    original_spread = c.realization.event.voice_onset_spread_beats
    intent = next(
        x
        for x in rhythmic_intents_for_candidate(
            c,
            phrase_boundary_probability=0.4,
            available_space_beats=0.0,
            drummer_activity=0.8,
        )
        if x.placement is RhythmicPlacement.ANTICIPATED
    )
    realized = apply_rhythmic_intent(c, intent)

    assert realized.realization.event.onset_offset_beats < 0
    assert realized.realization.event.voice_onset_spread_beats == pytest.approx(original_spread)
    assert realized.realization.event.annotations["rhythmic_placement"] == "anticipated"


def test_sustained_support_gets_sustained_variant():
    c = candidate(
        action=CompingActionType.SUSTAINED_SUPPORT,
        role=InteractionRole.SUPPORT,
        duration=1.0,
    )
    intents = rhythmic_intents_for_candidate(
        c,
        phrase_boundary_probability=0.2,
        available_space_beats=0.0,
        drummer_activity=0.3,
    )
    assert RhythmicPlacement.SUSTAINED in {x.placement for x in intents}


def test_silence_is_not_faked_as_rhythmic_sounding_variant():
    silence = PianoCompingCandidate(
        action_type=CompingActionType.SILENCE,
        role=InteractionRole.LAY_OUT,
        duration_beats=0.5,
    )
    assert rhythmic_intents_for_candidate(
        silence,
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        drummer_activity=0.5,
    ) == ()


def test_expansion_changes_timing_not_pitch_content():
    c = candidate()
    variants = expand_rhythmic_variants(
        c,
        phrase_boundary_probability=0.4,
        available_space_beats=0.0,
        drummer_activity=0.8,
    )
    assert len(variants) >= 3
    original = c.realization.event.pitches_midi
    assert all(v.realization.event.pitches_midi == original for v in variants)
    assert len({v.realization.event.onset_offset_beats for v in variants}) >= 3


def test_rhythmic_variants_remain_one_immediate_gesture_each():
    c = candidate()
    variants = expand_rhythmic_variants(
        c,
        phrase_boundary_probability=0.4,
        available_space_beats=0.0,
        drummer_activity=0.8,
    )
    for v in variants:
        assert not hasattr(v, "future_pattern")
        assert not hasattr(v, "future_events")
