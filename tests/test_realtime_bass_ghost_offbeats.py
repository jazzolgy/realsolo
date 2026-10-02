from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    InteractionKind,
    PlayerPresence,
    PlayerRole,
    TransportState,
)
from music_intelligence.reasoning.groove_context import GrooveFeel, build_groove_context
from music_intelligence.reasoning.interaction_scheduler import InteractionDirective
from realtime.ensemble_app.native_trio_players import Stage1BassNativeDecider


def _swing():
    return build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=120.0,
        grammar_id="swing.eighth_triplet_feel",
        subdivision_hint="swing_eighth",
    )


def test_realtime_bass_ghost_substep_is_percussive_not_second_walking_pitch():
    groove=_swing()
    beat=1.0+groove.swing_offbeat_fraction
    state=EnsembleState(
        transport=TransportState(
            beat=beat,
            bar=0,
            tempo_bpm=120.0,
            meter_numerator=4,
            meter_denominator=4,
        ),
        players=(
            PlayerPresence("bass","upright_bass",PlayerRole.BASS),
            PlayerPresence("drums","drum_kit",PlayerRole.DRUMS),
        ),
        ensemble_density=.20,
        ensemble_energy=.20,
        groove=groove,
    )
    decider=Stage1BassNativeDecider()
    decider.runner.last_ghost_opportunity=.90
    result=decider({
        "chord_symbol":"Cmaj7",
        "next_chord":"Dm7",
        "beat_in_bar":beat,
        "tempo_bpm":120.0,
        "beats_per_bar":4,
        "ensemble_snapshot":state,
        "interaction_directive":InteractionDirective(
            player_id="bass",
            interaction=InteractionKind.LOCK,
        ),
        "bass_mode":"walking",
        "bass_ghost_only":True,
    })
    assert result is not None
    assert result.gesture is not None
    assert "bass_ghost_note" in result.gesture.tags
    assert len(result.gesture.voices)==1
    voice=result.gesture.voices[0]
    assert voice.duration_beats < .25
    assert "ghost_note" in voice.articulation
    assert "eighth_offbeat" in voice.articulation


def test_realtime_ghost_substep_can_choose_space_instead_of_constant_eighths():
    groove=_swing()
    beat=1.0+groove.swing_offbeat_fraction
    state=EnsembleState(
        transport=TransportState(beat=beat,bar=0,tempo_bpm=120.0),
        players=(PlayerPresence("bass","upright_bass",PlayerRole.BASS),),
        ensemble_density=.95,
        ensemble_energy=.90,
        groove=groove,
    )
    decider=Stage1BassNativeDecider()
    decider.runner.last_ghost_opportunity=0.0
    result=decider({
        "chord_symbol":"Cmaj7",
        "beat_in_bar":beat,
        "tempo_bpm":120.0,
        "beats_per_bar":4,
        "ensemble_snapshot":state,
        "interaction_directive":InteractionDirective(
            player_id="bass",
            interaction=InteractionKind.HOLD_SPACE,
        ),
        "bass_mode":"walking",
        "bass_ghost_only":True,
    })
    assert result is not None
    assert result.gesture is None
    assert "bass_ghost_space" in result.tags
