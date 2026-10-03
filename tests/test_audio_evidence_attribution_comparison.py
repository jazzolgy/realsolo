from __future__ import annotations

from music_intelligence.audio_evidence import (
    AudioObservation,
    BoundedContextPosterior,
    compare_instrument_attribution,
)


def h(observation_id: str, probabilities):
    return BoundedContextPosterior().revise_instrument(
        AudioObservation(
            observation_id=observation_id,
            source_id="test",
            onset_seconds=0.0,
            nominal_midi=60.0,
            instrument_probabilities=probabilities,
        )
    )


def test_attribution_comparison_reports_ambiguity_change_without_ground_truth_claim():
    baseline = (
        h("a", {"bass": 0.48, "piano": 0.46, "other": 0.06}),
        h("b", {"piano": 0.90, "bass": 0.06, "other": 0.04}),
    )
    candidate = (
        h("a", {"bass": 0.78, "piano": 0.17, "other": 0.05}),
        h("b", {"bass": 0.72, "piano": 0.24, "other": 0.04}),
    )

    result = compare_instrument_attribution(baseline, candidate)

    assert result.baseline.ambiguous == 1
    assert result.candidate.ambiguous == 0
    assert result.ambiguity_fraction_delta == -0.5
    assert result.shared_observations == 2
    assert result.top_label_disagreements == 1
