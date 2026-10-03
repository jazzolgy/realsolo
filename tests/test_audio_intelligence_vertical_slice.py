import pytest

from music_intelligence.audio_intelligence import (
    AttributionFactor,
    AudioEventHypothesis,
    AutumnLeavesValidationCase,
    ConfidenceVector,
    PosteriorAttributor,
    RevisionLedger,
    to_structural_performance_data,
)


def ambiguous_low_f3():
    return AudioEventHypothesis(
        event_id="synthetic:be003:ambiguous-low-f3",
        source_id="BE-003",
        onset_time=120.0,
        duration=.42,
        pitch_midi=53.0,
        beat_position=206.5,
        bar_index=52,
        beat_in_bar=2.5,
        duration_beats=.72,
        instrument_probabilities={"bass": .48, "piano_lh": .46, "other": .06},
        role_probabilities={"time_floor": .55, "harmonic_support": .45},
        confidence=ConfidenceVector(
            pitch=.91,
            onset=.96,
            duration=.67,
            instrument=.48,
            alignment=.88,
        ),
        provenance=("validation_synthetic_case", "derived_only"),
    )


def test_context_revises_but_does_not_force_weak_acoustics():
    event = ambiguous_low_f3()
    attributor = PosteriorAttributor(max_context_log_shift=1.25)
    factors = (
        AttributionFactor(
            "temporal_continuity",
            {"bass": .8, "piano_lh": .18, "other": .02},
            .8,
        ),
        AttributionFactor(
            "simultaneous_piano_chord",
            {"bass": .75, "piano_lh": .20, "other": .05},
            .7,
        ),
        AttributionFactor(
            "score_harmony",
            {"bass": .62, "piano_lh": .35, "other": .03},
            .45,
        ),
    )
    revised = attributor.revise(event, factors)
    assert revised.top_instrument == "bass"
    assert revised.top_probability > .48
    assert revised.top_probability < .95
    assert revised.record.previous_probabilities["piano_lh"] == pytest.approx(.46)
    assert revised.event.confidence.pitch == pytest.approx(.91)
    assert revised.event.confidence.instrument == pytest.approx(
        revised.top_probability
    )


def test_ambiguous_revision_enters_hard_example_pool():
    event = ambiguous_low_f3()
    revised = PosteriorAttributor(max_context_log_shift=.15).revise(
        event,
        (
            AttributionFactor(
                "weak_context",
                {"bass": .52, "piano_lh": .45, "other": .03},
                .2,
            ),
        ),
    )
    ledger = RevisionLedger()
    ledger.record(revised)
    assert ledger.history_for(event.event_id)
    assert ledger.hard_examples


def test_bridge_preserves_factorized_confidence_and_probabilities():
    event = ambiguous_low_f3()
    revised = PosteriorAttributor().revise(
        event,
        (
            AttributionFactor(
                "continuity",
                {"bass": .90, "piano_lh": .08, "other": .02},
                1.0,
            ),
        ),
    )
    structural = to_structural_performance_data(
        "BE-003",
        (revised.event,),
        tempo_bpm=103.36,
        meter="4/4",
    )
    projected = structural.events[0]
    assert projected.instrument == "bass"
    assert projected.instrument_probabilities["bass"] == pytest.approx(
        revised.top_probability
    )
    assert projected.confidence_fields["pitch"] == pytest.approx(.91)
    assert projected.confidence_fields["duration"] == pytest.approx(.67)


def test_autumn_leaves_case_is_validation_metadata_not_ground_truth():
    case = AutumnLeavesValidationCase()
    assert case.source_id == "BE-003"
    assert case.rights_disposition == "DERIVED_ONLY"
    assert case.publication_class == "PUBLIC_DERIVED"
    assert case.pitch_hypotheses == 9742
    assert case.canonical_alignment_status == "unresolved"
