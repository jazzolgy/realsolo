from music_intelligence.legends import VocabularyMemoryItem, VocabularyUseType
from music_intelligence.legends.promotion import (
    VocabularyPromotionEvidence,
    VocabularyPromotionStatus,
    assess_vocabulary_promotion,
)


def item():
    return VocabularyMemoryItem(
        vocabulary_id="cell",
        source_id="recording_a",
        candidate_uses=frozenset({VocabularyUseType.ABSTRACTED_PATTERN}),
        confidence=0.9,
        provenance=("verified_source", "abstract_cell"),
    )


def test_timestamp_only_evidence_cannot_promote():
    decision = assess_vocabulary_promotion(
        item(),
        VocabularyPromotionEvidence(
            source_personnel_verified=True,
            phrase_context_verified=True,
            provenance_complete=True,
            dimension_confidence=0.95,
            detector_robustness=0.95,
            independent_window_count=3,
            independent_recording_count=2,
        ),
    )
    assert decision.status is VocabularyPromotionStatus.OBSERVATION_ONLY
    assert not decision.eligible_for_runtime


def test_structurally_grounded_recurrence_can_promote():
    decision = assess_vocabulary_promotion(
        item(),
        VocabularyPromotionEvidence(
            source_personnel_verified=True,
            phrase_context_verified=True,
            structural_coordinate_verified=True,
            provenance_complete=True,
            dimension_confidence=0.95,
            detector_robustness=0.90,
            independent_window_count=3,
            independent_recording_count=2,
            generic_pattern_risk=0.2,
        ),
    )
    assert decision.status is VocabularyPromotionStatus.ACTIVE_RUNTIME
    assert decision.eligible_for_runtime


def test_verified_intro_segment_can_count_as_musical_address():
    decision = assess_vocabulary_promotion(
        item(),
        VocabularyPromotionEvidence(
            source_personnel_verified=True,
            phrase_context_verified=True,
            arrangement_segment_verified=True,
            provenance_complete=True,
            dimension_confidence=0.95,
            manual_transcription_verified=True,
            independent_window_count=2,
            independent_recording_count=2,
        ),
    )
    assert decision.eligible_for_runtime
