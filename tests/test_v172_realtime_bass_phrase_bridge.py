from music_intelligence.reasoning.ensemble_state import (
    CommitmentState,
    EnsembleState,
    InteractionKind,
    PlayerActionIntent,
    PlayerPresence,
    PlayerRole,
    TransportState,
)
from music_intelligence.reasoning.interaction_scheduler import schedule_player
from realtime.ensemble_app.native_trio_players import Stage1BassNativeDecider
from realtime.ensemble_app.trio_adapters import BassRuntimeAdapter


def state(maturity):
    return EnsembleState(
        transport=TransportState(
            beat=1.0,
            bar=0,
            section="A",
            tempo_bpm=140.0,
            form_position=.2,
        ),
        players=(
            PlayerPresence("bass","bass",PlayerRole.BASS),
            PlayerPresence("solo","alto sax",PlayerRole.SOLOIST),
            PlayerPresence("drums","drums",PlayerRole.DRUMS),
            PlayerPresence("piano","piano",PlayerRole.COMPER),
        ),
        intents=(
            PlayerActionIntent(
                "solo",
                InteractionKind.LEAD,
                CommitmentState.COMMITTED,
                density=.55,
                energy=.60,
                tension=.50,
                leadership=.90,
                phrase_maturity=maturity,
            ),
        ),
        ensemble_density=.48,
        ensemble_energy=.55,
        ensemble_tension=.50,
        space_available=.45,
    )


def context():
    return {
        "chord_symbol":"Dm7",
        "next_chord":"G7",
        "beat_in_bar":1.0,
        "bar_index":0,
        "beats_per_bar":4,
        "tempo_bpm":140.0,
    }


def bass_phrase_annotation(maturity):
    s=state(maturity)
    adapter=BassRuntimeAdapter(Stage1BassNativeDecider())
    d=schedule_player(s,"bass")
    out=adapter.decide_immediate(snapshot=s,directive=d,context=context())
    assert out is not None and out.gestures
    return out.gestures[0].annotations["phrase_intent"]


def test_realtime_bass_consumes_soloist_phrase_maturity():
    assert bass_phrase_annotation(.08) == "ground"
    assert bass_phrase_annotation(.68) == "build"
