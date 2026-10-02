from music_intelligence.drums.bebop import BebopPhraseMemory, SoloistEnergyProjection
from music_intelligence.drums.bebop_runtime import (
    BebopRuntimeProjection,
    build_bebop_candidates,
    score_bebop_gesture,
)
from music_intelligence.drums.model import DrummerRuntimeContext, DrummerSoftPlan
from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    InteractionKind,
    PlayerActionIntent,
    PlayerPresence,
    PlayerRole,
    TransportState,
    update_player_intent,
)


def ensemble_with_walking_bass():
    state = EnsembleState(
        transport=TransportState(beat=1.0, bar=4, section="A"),
        players=(
            PlayerPresence("bass", "acoustic_bass", PlayerRole.BASS),
            PlayerPresence("drums", "drums", PlayerRole.DRUMS),
            PlayerPresence("sax", "alto_sax", PlayerRole.SOLOIST),
        ),
    )
    return update_player_intent(
        state,
        PlayerActionIntent(
            "bass",
            InteractionKind.LOCK,
            density=0.86,
            energy=0.65,
            tags=frozenset({"walking", "quarter_note_pulse"}),
        ),
    )


def test_bebop_projection_can_read_shared_bass_state_without_core_mutation():
    state = ensemble_with_walking_bass()
    projection = BebopRuntimeProjection.from_ensemble_state(
        soloist=SoloistEnergyProjection(0.5, 0.55, 0.0),
        phrase_memory=BebopPhraseMemory(),
        ensemble_state=state,
    )
    assert projection.bass is not None
    assert projection.bass.walking_confidence == 1.0
    assert state.generation == 1


def test_walking_bass_changes_kick_floor_score_but_not_by_forcing_alignment():
    state = ensemble_with_walking_bass()
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}), energy=0.4)
    context = DrummerRuntimeContext(position_in_bar_beats=0.0, phrase_position=0.4)

    with_bass = BebopRuntimeProjection.from_ensemble_state(
        soloist=SoloistEnergyProjection(0.4, 0.5, 0.0),
        phrase_memory=BebopPhraseMemory(),
        ensemble_state=state,
    )
    without_bass = BebopRuntimeProjection(
        soloist=SoloistEnergyProjection(0.4, 0.5, 0.0),
        phrase_memory=BebopPhraseMemory(),
    )

    candidates = build_bebop_candidates(plan, context, with_bass)
    floor = next(g for g in candidates if "bass_floor_support" in g.tags)

    score_with = score_bebop_gesture(floor, plan, context, with_bass)
    score_without = score_bebop_gesture(floor, plan, context, without_bass)

    assert score_with.score < score_without.score
    assert any(name == "bass_floor_complementarity" for name, _ in score_with.components)


def test_walking_bass_can_reward_ride_freedom():
    state = ensemble_with_walking_bass()
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}))
    context = DrummerRuntimeContext(position_in_bar_beats=0.0, phrase_position=0.3)
    projection = BebopRuntimeProjection.from_ensemble_state(
        soloist=SoloistEnergyProjection(0.4, 0.5, 0.0),
        phrase_memory=BebopPhraseMemory(),
        ensemble_state=state,
    )

    time = next(
        g for g in build_bebop_candidates(plan, context, projection)
        if g.role.value == "time"
    )
    scored = score_bebop_gesture(time, plan, context, projection)

    assert any(name == "bass_enables_ride_freedom" for name, _ in scored.components)
