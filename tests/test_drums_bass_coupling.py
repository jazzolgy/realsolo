from music_intelligence.drums.bass_coupling import (
    coupling_score_adjustment,
    infer_bass_drums_coupling,
    project_bass_pulse,
)
from music_intelligence.drums.bebop import BassDrumIntent, BebopInteractionState
from music_intelligence.drums.model import DrumGesture, DrumHit, DrumVoice, GestureRole, Limb
from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    InteractionKind,
    PlayerActionIntent,
    PlayerPresence,
    PlayerRole,
    TransportState,
    update_player_intent,
)


def base_state():
    return EnsembleState(
        transport=TransportState(beat=1.0, bar=8, section="A"),
        players=(
            PlayerPresence("bass", "acoustic_bass", PlayerRole.BASS),
            PlayerPresence("drums", "drums", PlayerRole.DRUMS),
            PlayerPresence("sax", "alto_sax", PlayerRole.SOLOIST),
        ),
    )


def walking_state():
    state = base_state()
    return update_player_intent(
        state,
        PlayerActionIntent(
            "bass",
            InteractionKind.LOCK,
            density=0.82,
            energy=0.62,
            phrase_maturity=0.4,
            tags=frozenset({"walking", "quarter_note_pulse"}),
        ),
    )


def test_walking_bass_projects_strong_shared_pulse():
    projection = project_bass_pulse(walking_state())
    assert projection.present
    assert projection.walking_confidence == 1.0
    assert projection.pulse_confidence > 0.75


def test_strong_walking_bass_reduces_need_for_kick_floor_duplication():
    coupling = infer_bass_drums_coupling(
        project_bass_pulse(walking_state()),
        interaction_state=BebopInteractionState.SUPPORT,
    )
    assert coupling.shared_pulse > 0.7
    assert coupling.floor_support_need < 0.4
    assert coupling.drummer_freedom > 0.7


def test_missing_bass_increases_floor_support_need():
    no_bass = EnsembleState(
        transport=TransportState(beat=1.0, bar=1),
        players=(PlayerPresence("drums", "drums", PlayerRole.DRUMS),),
    )
    coupling = infer_bass_drums_coupling(
        project_bass_pulse(no_bass),
        interaction_state=BebopInteractionState.SUPPORT,
    )
    assert coupling.floor_support_need > 0.6


def test_low_end_overlap_penalizes_unneeded_bass_drum_floor():
    coupling = infer_bass_drums_coupling(
        project_bass_pulse(walking_state()),
        interaction_state=BebopInteractionState.SUPPORT,
    )
    kick = DrumGesture(
        hits=(DrumHit(DrumVoice.BASS_DRUM, Limb.RIGHT_FOOT, 34, articulation="floor_support"),),
        role=GestureRole.COMP,
        tags=frozenset({"bass_floor_support"}),
    )
    adjustment, parts = coupling_score_adjustment(
        kick,
        bass_intent=BassDrumIntent.FLOOR_SUPPORT,
        coupling=coupling,
    )
    assert adjustment < 0
    assert any(name == "bass_floor_complementarity" for name, _ in parts)


def test_explicit_bass_figure_can_create_alignment_opportunity():
    state = base_state()
    state = update_player_intent(
        state,
        PlayerActionIntent(
            "bass",
            InteractionKind.PUNCTUATE,
            density=0.5,
            energy=0.7,
            phrase_maturity=0.9,
            tags=frozenset({"ensemble_kick", "figure"}),
        ),
    )
    coupling = infer_bass_drums_coupling(
        project_bass_pulse(state),
        interaction_state=BebopInteractionState.HANDOFF,
    )
    assert coupling.accent_alignment_opportunity > 0.7
