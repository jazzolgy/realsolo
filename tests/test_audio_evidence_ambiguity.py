from __future__ import annotations

from music_intelligence.audio_evidence import (
    AudioObservation,
    BoundedContextPosterior,
    summarize_instrument_ambiguity,
)


def hypothesis(observation_id: str, probabilities):
    return BoundedContextPosterior().revise_instrument(
        AudioObservation(
            observation_id=observation_id,
            source_id="test",
            onset_seconds=0.0,
            nominal_midi=60.0,
            instrument_probabilities=probabilities,
        )
    )


def test_ambiguity_summary_uses_same_commitment_thresholds_as_adapter():
    clear = hypothesis("clear", {"piano": 0.90, "bass": 0.06, "other": 0.04})
    close = hypothesis("close", {"bass": 0.48, "piano": 0.46, "other": 0.06})
    weak = hypothesis("weak", {"piano": 0.60, "bass": 0.20, "other": 0.20})

    summary = summarize_instrument_ambiguity((clear, close, weak))

    assert summary.total == 3
    assert summary.ambiguous == 2
    assert summary.ambiguous_fraction == 2 / 3
    assert summary.minimum_top_probability == 0.70
    assert summary.minimum_margin == 0.15
