from music_intelligence.reasoning.groove_context import (
    EnsembleTempoState,
    GrooveCoordinationMode,
    GrooveFeel,
    build_groove_context,
    evolve_ensemble_tempo,
    player_phase_offset_beats,
    player_swing_offbeat_fraction,
)


def test_locked_mode_collapses_player_phase_to_shared_reference():
    groove=build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=120.0,
        coordination_mode=GrooveCoordinationMode.LOCKED,
    )
    assert player_phase_offset_beats("bass",groove,phrase_maturity=.2)==0.0
    assert player_phase_offset_beats("piano",groove,phrase_maturity=.8)==0.0
    assert player_swing_offbeat_fraction("bass",groove)==groove.swing_offbeat_fraction
    assert player_swing_offbeat_fraction("drums",groove)==groove.swing_offbeat_fraction


def test_elastic_mode_keeps_common_pulse_but_allows_role_specific_placement():
    groove=build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=120.0,
        coordination_mode=GrooveCoordinationMode.ELASTIC,
        phase_elasticity=.8,
        swing_elasticity=.8,
    )
    bass=player_phase_offset_beats("bass",groove,phrase_maturity=.5)
    piano=player_phase_offset_beats("piano",groove,phrase_maturity=.5)
    sax=player_phase_offset_beats("tenor_sax",groove,phrase_maturity=.5)
    assert len({round(bass,6),round(piano,6),round(sax,6)})==3
    assert abs(bass)<.08 and abs(piano)<.08 and abs(sax)<.08
    assert player_swing_offbeat_fraction("bass",groove) != player_swing_offbeat_fraction("piano",groove)


def test_phrase_position_changes_player_placement_smoothly_not_randomly():
    groove=build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=120.0,
        coordination_mode=GrooveCoordinationMode.ELASTIC,
        phase_elasticity=1.0,
    )
    early=player_phase_offset_beats("tenor_sax",groove,phrase_maturity=.1)
    late=player_phase_offset_beats("tenor_sax",groove,phrase_maturity=.95)
    assert early < late
    assert player_phase_offset_beats("tenor_sax",groove,phrase_maturity=.1)==early


def test_human_drift_moves_reference_tempo_gradually():
    groove=build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=120.0,
        coordination_mode=GrooveCoordinationMode.HUMAN_DRIFT,
        tempo_elasticity=1.0,
    )
    state=EnsembleTempoState(120.0,120.0,120.0)
    for _ in range(8):
        state=evolve_ensemble_tempo(state,groove,collective_push=.9)
    assert 120.0 < state.current_tempo_bpm < 123.1
    pushed=state.current_tempo_bpm
    for _ in range(8):
        state=evolve_ensemble_tempo(state,groove,collective_push=-.6,phrase_release=.8)
    assert state.current_tempo_bpm < pushed


def test_locked_and_elastic_do_not_drift_transport_tempo():
    for mode in (GrooveCoordinationMode.LOCKED,GrooveCoordinationMode.ELASTIC):
        groove=build_groove_context(
            GrooveFeel.SWING,
            tempo_bpm=120.0,
            coordination_mode=mode,
            tempo_elasticity=1.0,
        )
        state=evolve_ensemble_tempo(
            EnsembleTempoState(120.0,121.0,122.0),
            groove,
            collective_push=1.0,
        )
        assert state.current_tempo_bpm==120.0
        assert state.target_tempo_bpm==120.0
