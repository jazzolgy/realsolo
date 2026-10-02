from music_intelligence.reasoning.groove_context import (
    GrooveFeel,
    build_groove_context,
    groove_timing_offset_beats,
)
from music_intelligence.reasoning.solo_candidates import SoloCandidateSpec
from music_intelligence.reasoning.solo_expression import SoloExpressionIntent
from music_intelligence.reasoning.ensemble_state import (
    CommitmentState,
    EnsembleState,
    InteractionKind,
    PlayerActionIntent,
    PlayerPresence,
    PlayerRole,
    TransportState,
    update_player_intent,
)
from players.piano.solo_realizer import PianoSoloRealizer, PianoSoloRealizerContext
from players.bass.solo_realizer import BassSoloRealizer, BassSoloRealizerContext
from players.sax.solo_realizer import SaxSoloRealizer, SaxSoloRealizerContext
from players.drums.solo_realizer import DrumSoloRealizer, DrumSoloRealizerContext
from players.drums.model import (
    DrummerRuntimeContext,
    DrummerSoftPlan,
    GestureRole,
)
from players.drums.online_drummer import build_immediate_candidates


def _swing():
    return build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=120.0,
        grammar_id="swing.eighth_triplet_feel",
        subdivision_hint="swing_eighth",
    )


def test_all_solo_players_share_same_swing_offbeat_reference():
    groove=_swing()
    candidate=SoloCandidateSpec(0,0.5)
    expression=SoloExpressionIntent()
    expected=groove_timing_offset_beats(0.5,groove)
    assert expected > 0.0

    piano=PianoSoloRealizer().realize(
        candidate,expression,
        PianoSoloRealizerContext(beat_position_beats=0.5,groove=groove),
    )
    bass=BassSoloRealizer().realize(
        candidate,expression,
        BassSoloRealizerContext(beat_position_beats=0.5,groove=groove),
    )
    sax=SaxSoloRealizer().realize(
        candidate,expression,
        SaxSoloRealizerContext(beat_position_beats=0.5,groove=groove),
    )
    drums=DrumSoloRealizer().realize(
        candidate,expression,
        DrumSoloRealizerContext(beat_position_beats=0.5,groove=groove),
    )

    assert abs(piano.event.onset_offset_beats-expected) < 1e-9
    assert abs(bass.event.onset_offset_beats-expected) < 1e-9
    assert abs(sax.event.onset_offset_beats-expected) < 1e-9
    assert abs(drums.gesture.hits[0].onset_offset_beats-expected) < 1e-9
    assert "groove:swing" in piano.event.tags
    assert "groove:swing" in bass.event.tags
    assert "groove:swing" in sax.event.tags
    assert "groove:swing" in drums.gesture.tags


def test_straight_context_does_not_get_swing_warp():
    groove=build_groove_context(GrooveFeel.STRAIGHT,tempo_bpm=120.0)
    assert groove_timing_offset_beats(0.5,groove) == 0.0


def test_shared_groove_survives_ensemble_intent_publication():
    groove=_swing()
    state=EnsembleState(
        transport=TransportState(beat=0.0,bar=0,tempo_bpm=120.0),
        players=(PlayerPresence("piano","piano",PlayerRole.COMPER),),
        groove=groove,
    )
    nxt=update_player_intent(
        state,
        PlayerActionIntent(
            "piano",
            InteractionKind.SUPPORT,
            commitment=CommitmentState.COMMITTED,
        ),
    )
    assert nxt.groove == groove


def test_shared_straight_overrides_drummer_default_swing_timekeeping():
    straight=build_groove_context(GrooveFeel.STRAIGHT,tempo_bpm=120.0)
    context=DrummerRuntimeContext(
        position_in_bar_beats=0.0,
        tempo_bpm=120.0,
        groove=straight,
    )
    candidates=build_immediate_candidates(DrummerSoftPlan(),context)
    assert all("swing" not in g.tags for g in candidates)
    # Player's local default may still say SWING, but Shared groove owns the ensemble feel.
    assert not any(g.role is GestureRole.TIME and "timekeeping" in g.tags for g in candidates)


def test_swing_ratio_is_tempo_conditioned_but_shared():
    slow=build_groove_context(GrooveFeel.SWING,tempo_bpm=80.0)
    fast=build_groove_context(GrooveFeel.SWING,tempo_bpm=280.0)
    assert slow.swing_offbeat_fraction > fast.swing_offbeat_fraction
    assert fast.swing_offbeat_fraction > 0.5
