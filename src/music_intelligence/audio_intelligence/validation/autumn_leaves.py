"""Public-safe validation metadata for the first Shared Audio Intelligence case."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from ..schemas.evidence import AudioEventHypothesis


@dataclass(frozen=True)
class AutumnLeavesValidationCase:
    source_id: str = "BE-003"
    track_start_s: float = 708.0
    track_end_s: float = 1069.0
    rights_disposition: str = "DERIVED_ONLY"
    harmonic_onsets: int = 2000
    pitch_hypotheses: int = 9742
    percussive_events: int = 1311
    pulse_bpm_estimate: float = 103.36
    canonical_alignment_status: str = "unresolved"


def summarize_validation_events(
    events: Iterable[AudioEventHypothesis],
) -> dict[str, float | int]:
    seq = tuple(events)
    for event in seq:
        event.validate()

    instrument_conf = [
        event.confidence.instrument
        for event in seq
        if event.confidence.instrument is not None
    ]
    alignment_conf = [
        event.confidence.alignment
        for event in seq
        if event.confidence.alignment is not None
    ]
    ambiguous = 0
    for event in seq:
        ranked = sorted(event.instrument_probabilities.values(), reverse=True)
        if len(ranked) >= 2 and (
            ranked[0] < 0.70 or ranked[0] - ranked[1] < 0.15
        ):
            ambiguous += 1

    return {
        "event_count": len(seq),
        "ambiguous_instrument_events": ambiguous,
        "mean_instrument_confidence": mean(instrument_conf) if instrument_conf else 0.0,
        "mean_alignment_confidence": mean(alignment_conf) if alignment_conf else 0.0,
    }
