from music_intelligence.legends import (
    VocabularyMemoryItem,
    VocabularyUseType,
)
from music_intelligence.legends.promotion import (
    VocabularyPromotionEvidence,
    VocabularyPromotionStatus,
    active_runtime_items,
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


def test_single_detector_sensitive_window_cannot_enter_runtime():
    decision = assess_vocabulary_promotion(
        item(),
        VocabularyPromotionEvidence(
            source_personnel_verified=True,
            phrase_context_verified=True,
            structural_coordinate_verified=True,
            provenance_complete=True,
            dimension_confidence=0.9,
            detector_robustness=0.2,
            independent_window_count=1,
            independent_recording_count=1,
        ),
    )
    assert decision.status is VocabularyPromotionStatus.VOCABULARY_CANDIDATE
    assert not decision.eligible_for_runtime


def test_independent_recording_recurrence_can_promote_robust_item():
    decision = assess_vocabulary_promotion(
        item(),
        VocabularyPromotionEvidence(
            source_personnel_verified=True,
            phrase_context_verified=True,
            structural_coordinate_verified=True,
            provenance_complete=True,
            dimension_confidence=0.91,
            detector_robustness=0.88,
            independent_window_count=3,
            independent_recording_count=2,
            generic_pattern_risk=0.25,
        ),
    )
    assert decision.status is VocabularyPromotionStatus.ACTIVE_RUNTIME
    assert decision.eligible_for_runtime


def test_generic_pattern_can_be_validated_without_becoming_legend_signature():
    decision = assess_vocabulary_promotion(
        item(),
        VocabularyPromotionEvidence(
            source_personnel_verified=True,
            phrase_context_verified=True,
            structural_coordinate_verified=True,
            provenance_complete=True,
            dimension_confidence=0.95,
            detector_robustness=0.95,
            independent_window_count=5,
            independent_recording_count=3,
            generic_pattern_risk=0.9,
        ),
    )
    assert decision.status is VocabularyPromotionStatus.VALIDATED
    assert not decision.eligible_for_runtime


def test_active_runtime_filter_requires_explicit_evidence():
    candidate = item()
    assert active_runtime_items((candidate,), {}) == ()
