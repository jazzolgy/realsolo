from realtime.ensemble_app.instrument_discovery import (
    InstrumentEvidence,
    InstrumentPromotionPolicy,
    build_instrument_profile_candidate,
)


def ev(source_id: str, confidence: float = 0.9, count: int = 5, duration: float = 12.0):
    return InstrumentEvidence(
        source_id=source_id,
        instrument_label="trombone",
        family_label="brass",
        confidence=confidence,
        occurrence_count=count,
        duration_s=duration,
        role_probabilities={"solo": 0.7, "ensemble": 0.3},
    )


def test_single_source_does_not_promote_new_instrument():
    assert build_instrument_profile_candidate([ev("one")]) is None


def test_repeated_cross_source_evidence_promotes_candidate():
    candidate=build_instrument_profile_candidate([ev("a"),ev("b"),ev("c")])
    assert candidate is not None
    assert candidate.instrument_label == "trombone"
    assert candidate.family_label == "brass"
    assert candidate.distinct_sources == 3
    assert candidate.total_occurrences == 15


def test_low_confidence_is_not_promoted():
    rows=[ev("a",0.5),ev("b",0.5),ev("c",0.5)]
    assert build_instrument_profile_candidate(rows) is None
