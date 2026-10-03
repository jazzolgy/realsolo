import dataclasses

import pytest

from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    InteractionEvent,
    InteractionKind,
    PlayerPresence,
    PlayerRole,
    TransportState,
)
from music_intelligence.reasoning.groove_context import (
    GrooveFeel,
    GrooveTemporalContext,
)
from music_intelligence.reasoning.musical_moment import (
    MomentActionCommitment,
    MomentHarmony,
    MomentPhraseState,
    MomentPlayerAction,
    MusicalMoment,
    musical_moment_from_ensemble_state,
)


def test_musical_moment_aligns_form_harmony_phrase_and_players():
    moment=MusicalMoment(
        moment_id="alice:chorus2:A:bar5",
        position=__import__(
            "music_intelligence.reasoning.musical_moment",
            fromlist=["MomentPosition"],
        ).MomentPosition(
            beat=16.0,
            bar=5,
            section="A",
            chorus=2,
            form_position=.25,
        ),
        harmony=MomentHarmony(
            expected_ref="harm:expected:5",
            observed_ref="harm:observed:5",
            inferred_ref="harm:inferred:5",
            tension=.55,
            confidence=.9,
        ),
        phrase=MomentPhraseState(
            phrase_id="lafaro:p12",
            maturity=.62,
            space=.7,
            tension=.58,
            motif_id="motif:ascending-cell",
            confidence=.85,
        ),
        player_actions=(
            MomentPlayerAction(
                "piano","piano",role="soloist",action_type="leave_space",
                density=.2,energy=.45,space=.8,confidence=.9,
            ),
            MomentPlayerAction(
                "bass","bass",role="foreground",action_type="foreground_entry",
                interaction="answer",density=.65,energy=.7,tension=.6,
                register_center=.68,phrase_role="develop",
                motif_id="motif:ascending-cell",
                commitment=MomentActionCommitment.PLAYED,
                confidence=.88,
            ),
            MomentPlayerAction(
                "drums","drum_set",role="support",action_type="time_support",
                density=.5,energy=.55,confidence=.85,
            ),
        ),
        ensemble_density=.48,
        ensemble_energy=.58,
        ensemble_tension=.52,
        space_available=.42,
        confidence=.86,
    )
    moment.validate()
    assert moment.harmony.expected_ref == "harm:expected:5"
    assert {x.instrument for x in moment.player_actions} == {"piano","bass","drum_set"}


def test_musical_moment_contains_no_player_realization_commands():
    moment_fields={x.name for x in dataclasses.fields(MusicalMoment)}
    action_fields={x.name for x in dataclasses.fields(MomentPlayerAction)}
    forbidden={
        "pitch_midi","pitch_class","voicing","string","fret","limb",
        "ride_hit","snare_hit","kick_hit","render_event",
    }
    assert not moment_fields & forbidden
    assert not action_fields & forbidden


def test_snapshot_from_ensemble_state_does_not_invent_new_musical_meaning():
    state=EnsembleState(
        transport=TransportState(
            beat=12.5,
            bar=4,
            section="B",
            chorus=1,
            form_position=.5,
        ),
        players=(
            PlayerPresence("piano","piano",PlayerRole.SOLOIST),
            PlayerPresence("bass","bass",PlayerRole.BASS),
        ),
        recent_interactions=(
            InteractionEvent(
                "bass",
                InteractionKind.ANSWER,
                target_player_ids=("piano",),
                confidence=.8,
            ),
        ),
        harmonic_state_id="harmonic-state:42",
        ensemble_density=.6,
        ensemble_energy=.7,
        ensemble_tension=.4,
        space_available=.3,
        groove=GrooveTemporalContext(
            feel=GrooveFeel.SWING,
            grammar_id="swing",
            groove_strength=.9,
            confidence=.85,
        ),
    )
    moment=musical_moment_from_ensemble_state(
        state,
        moment_id="runtime:42",
        confidence=.8,
    )
    assert moment.position.bar == 4
    assert moment.harmony.inferred_ref == "harmonic-state:42"
    assert moment.harmony.confidence == 0.0
    assert moment.interactions[0].kind == "answer"
    assert moment.groove.grammar_id == "swing"


def test_register_center_is_normalized_not_instrument_specific_pitch():
    action=MomentPlayerAction(
        player_id="bass",
        instrument="bass",
        register_center=.72,
        confidence=.8,
    )
    action.validate()
    with pytest.raises(ValueError):
        MomentPlayerAction(
            player_id="bass",
            instrument="bass",
            register_center=48.0,
            confidence=.8,
        ).validate()


def test_moment_does_not_encode_causal_or_quality_judgment():
    fields={x.name for x in dataclasses.fields(MusicalMoment)}
    forbidden={
        "reward","success","failure","quality_score",
        "causal_attribution","caused_by","good_bad",
    }
    assert not fields & forbidden
