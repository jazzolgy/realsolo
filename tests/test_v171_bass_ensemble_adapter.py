from music_intelligence.reasoning.ensemble_state import (
    CommitmentState,
    EnsembleState,
    InteractionKind,
    PlayerActionIntent,
    PlayerPresence,
    PlayerRole,
    TransportState,
)
from players.bass.ensemble_adapter import derive_bass_ensemble_signals


def state(*, maturity=.5, density=.5, energy=.5, drum_fill=False):
    players=(
        PlayerPresence("bass","bass",PlayerRole.BASS),
        PlayerPresence("solo","alto sax",PlayerRole.SOLOIST),
        PlayerPresence("drums","drums",PlayerRole.DRUMS),
        PlayerPresence("piano","piano",PlayerRole.COMPER),
    )
    intents=[
        PlayerActionIntent(
            "solo",
            InteractionKind.LEAD,
            CommitmentState.COMMITTED,
            density=.55,
            energy=.6,
            leadership=.9,
            phrase_maturity=maturity,
        )
    ]
    if drum_fill:
        intents.append(PlayerActionIntent(
            "drums",
            InteractionKind.SETUP,
            CommitmentState.COMMITTED,
            density=.7,
            energy=.75,
            leadership=.1,
            phrase_maturity=.2,
        ))
    return EnsembleState(
        transport=TransportState(beat=0,bar=1),
        players=players,
        intents=tuple(intents),
        ensemble_density=density,
        ensemble_energy=energy,
        ensemble_tension=.5,
        space_available=.4,
    )


def test_leader_phrase_maturity_becomes_bass_phrase_progress():
    sig=derive_bass_ensemble_signals(state(maturity=.64),bass_player_id="bass")
    assert sig.phrase_progress == .64
    assert sig.soloist_phrase_ending is False


def test_mature_solo_phrase_opens_ending_signal():
    sig=derive_bass_ensemble_signals(state(maturity=.82),bass_player_id="bass")
    assert sig.soloist_phrase_ending is True


def test_drum_setup_is_detected_as_fill():
    sig=derive_bass_ensemble_signals(state(drum_fill=True),bass_player_id="bass")
    assert sig.drum_fill_active is True


def test_shared_density_and_energy_become_bass_activity():
    sig=derive_bass_ensemble_signals(
        state(density=.8,energy=.6),
        bass_player_id="bass",
    )
    assert .7 < sig.ensemble_activity < .8
