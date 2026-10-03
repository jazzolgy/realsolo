import pytest

from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    PerformedPitch,
    PerformanceCommitment,
    PerformanceTimeSpan,
    ProbabilityEstimate,
)
from music_intelligence.transcribe.evidence_diagnostics import (
    CorrectionRiskLevel,
    analyze_event_correction,
    total_variation_distance,
)


def _event(raw, posterior):
    return CommittedPerformanceEvent(
        event_id="diagnostic:1",
        player_id="source",
        instrument="unknown",
        commitment=PerformanceCommitment.PLAYED,
        time=PerformanceTimeSpan(0.0, 0.2),
        pitch=PerformedPitch(nominal_midi=43),
        raw_instrument_probabilities=tuple(
            ProbabilityEstimate(label, probability) for label, probability in raw
        ),
        context_instrument_probabilities=tuple(
            ProbabilityEstimate(label, probability) for label, probability in posterior
        ),
    )


def test_small_agreeing_correction_is_low_risk():
    report = analyze_event_correction(
        _event(
            (("bass", .88), ("kick", .12)),
            (("bass", .93), ("kick", .07)),
        )
    )
    shift = report.instrument_shift
    assert shift is not None
    assert shift.raw_top_label == "bass"
    assert shift.posterior_top_label == "bass"
    assert shift.risk_level is CorrectionRiskLevel.LOW
    assert not shift.context_dominated
    assert not report.review_recommended


def test_large_context_driven_shift_is_flagged_for_review():
    report = analyze_event_correction(
        _event(
            (("bass", .28), ("kick", .62), ("piano", .10)),
            (("bass", .91), ("kick", .06), ("piano", .03)),
        )
    )
    shift = report.instrument_shift
    assert shift is not None
    assert shift.top_label_changed
    assert shift.context_dominated
    assert shift.posterior_label_lift == pytest.approx(.63)
    assert shift.risk_level is CorrectionRiskLevel.HIGH
    assert report.review_recommended


def test_moderate_top_label_flip_is_not_automatically_called_hallucination():
    report = analyze_event_correction(
        _event(
            (("bass", .46), ("kick", .44), ("piano", .10)),
            (("bass", .40), ("kick", .52), ("piano", .08)),
        )
    )
    shift = report.instrument_shift
    assert shift is not None
    assert shift.top_label_changed
    assert shift.risk_level is CorrectionRiskLevel.MODERATE
    assert not shift.context_dominated
    assert not shift.review_recommended


def test_total_variation_handles_labels_appearing_only_after_context():
    raw = (
        ProbabilityEstimate("bass_attack", .48),
        ProbabilityEstimate("percussive_noise", .42),
        ProbabilityEstimate("unknown", .10),
    )
    posterior = (
        ProbabilityEstimate("bass_ghost_dead_note", .81),
        ProbabilityEstimate("other_percussion", .13),
        ProbabilityEstimate("unknown", .06),
    )
    assert total_variation_distance(raw, posterior) == pytest.approx(.94)
