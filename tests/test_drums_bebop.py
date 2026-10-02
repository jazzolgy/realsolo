from music_intelligence.drums.bebop import (
    BebopCompIntent,
    BebopInteractionState,
    BebopPhraseMemory,
    SoloistEnergyProjection,
    choose_comp_intent,
    infer_bebop_interaction_state,
)
from music_intelligence.drums.bebop_annotation import (
    BebopPhraseAnnotation,
    DrumEventKind,
    EvidenceConfidence,
    BebopEventAnnotation,
)
from music_intelligence.drums.bebop import BebopTimeIntent


def test_rising_soloist_can_build_when_drummer_has_headroom():
    decision = infer_bebop_interaction_state(
        SoloistEnergyProjection(0.65, 0.65, 0.4),
        BebopPhraseMemory(recent_comp_density=0.15, recent_response_count=0),
        drummer_energy=0.45,
        phrase_position=0.5,
    )
    assert decision.state is BebopInteractionState.BUILD


def test_rising_soloist_can_coast_when_drummer_was_already_active():
    decision = infer_bebop_interaction_state(
        SoloistEnergyProjection(0.8, 0.8, 0.35),
        BebopPhraseMemory(recent_comp_density=0.75, recent_response_count=4),
        drummer_energy=0.75,
        phrase_position=0.5,
    )
    assert decision.state is BebopInteractionState.COAST
    assert choose_comp_intent(decision, BebopPhraseMemory(recent_comp_density=0.75), phrase_position=0.5) is BebopCompIntent.INTENTIONAL_NON_RESPONSE


def test_post_climax_energy_drop_yields_come_down():
    decision = infer_bebop_interaction_state(
        SoloistEnergyProjection(0.6, 0.7, -0.3, climax_probability=0.85),
        BebopPhraseMemory(recent_comp_density=0.6),
        drummer_energy=0.8,
        phrase_position=0.65,
    )
    assert decision.state is BebopInteractionState.COME_DOWN


def test_phrase_annotation_preserves_periodicity_ambiguity_and_ear_verification():
    annotation = BebopPhraseAnnotation(
        source_audio="parker_compilation",
        start_s=100.0,
        end_s=110.0,
        periodicity_bpm=120.0,
        periodicity_ambiguous=True,
        time_intent=BebopTimeIntent.HOLD_PULSE,
        comp_intent=BebopCompIntent.SUPPORT,
        interaction_state=BebopInteractionState.LISTEN,
        verified_by_ear=False,
        events=(
            BebopEventAnnotation(105.0, DrumEventKind.UNKNOWN_PERCUSSIVE, EvidenceConfidence.MEDIUM),
        ),
    )
    annotation.validate()
    assert annotation.periodicity_ambiguous is True
    assert annotation.verified_by_ear is False
