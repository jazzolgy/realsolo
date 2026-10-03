"""Conservative acoustic instrument priors from pitch register and timbre.

This is a baseline evidence generator, not a musical-role classifier. It uses
only detector-side acoustic features and intentionally leaves low-register
Bass-vs-Piano hypotheses ambiguous when the evidence is weak.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..adapters.source import AudioSource
from .contracts import (
    InstrumentDetection,
    OnsetDetection,
    PitchDetection,
    TimbreDetection,
    UnpitchedDetection,
)


def _normalize(values: dict[str, float]) -> dict[str, float]:
    total = sum(values.values())
    if total <= 0.0:
        raise ValueError("instrument prior requires positive probability mass")
    return {key: value / total for key, value in values.items()}


@dataclass
class AcousticInstrumentPriorDetector:
    """Generate weak target-specific priors without musical-context reasoning."""

    detector_id: str = "acoustic-register-timbre-prior:v0.1"

    def detect_instruments(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
        pitches: Sequence[PitchDetection] = (),
        unpitched: Sequence[UnpitchedDetection] = (),
        timbre: Sequence[TimbreDetection] = (),
    ) -> Sequence[InstrumentDetection]:
        del source
        by_onset_timbre = {
            item.onset_id: item for item in timbre
        }
        valid_onsets = {item.onset_id for item in onsets}
        results: list[InstrumentDetection] = []

        for pitch in pitches:
            if pitch.onset_id not in valid_onsets:
                continue
            midi = pitch.nominal_midi
            if midi is None and pitch.frequency_hz is not None:
                import math
                midi = 69.0 + 12.0 * math.log2(pitch.frequency_hz / 440.0)
            if midi is None:
                continue

            if midi <= 43.0:
                weights = {"bass": 0.56, "piano": 0.34, "other": 0.10}
            elif midi <= 52.0:
                weights = {"bass": 0.47, "piano": 0.43, "other": 0.10}
            elif midi <= 60.0:
                weights = {"bass": 0.28, "piano": 0.62, "other": 0.10}
            else:
                weights = {"bass": 0.08, "piano": 0.82, "other": 0.10}

            timbre_item = by_onset_timbre.get(pitch.onset_id)
            centroid = (
                timbre_item.spectral_centroid_hz
                if timbre_item is not None
                else None
            )
            if centroid is not None:
                if centroid < 900.0:
                    weights["bass"] *= 1.18
                    weights["piano"] *= 0.92
                elif centroid > 2200.0:
                    weights["bass"] *= 0.82
                    weights["piano"] *= 1.12

            probabilities = _normalize(weights)
            ordered = sorted(probabilities.values(), reverse=True)
            confidence = (
                ordered[0] - ordered[1]
                if len(ordered) > 1
                else ordered[0]
            )
            results.append(
                InstrumentDetection(
                    onset_id=pitch.onset_id,
                    target_id=pitch.pitch_id,
                    probabilities=probabilities,
                    confidence=confidence,
                    detector_id=self.detector_id,
                )
            )

        unpitched_index: dict[str, int] = {}
        for token in unpitched:
            if token.onset_id not in valid_onsets:
                continue
            unpitched_index[token.onset_id] = (
                unpitched_index.get(token.onset_id, 0) + 1
            )
            target_id = (
                token.onset_id
                + ":unpitched:"
                + str(unpitched_index[token.onset_id])
            )
            probabilities = {"drums": 0.88, "other": 0.12}
            results.append(
                InstrumentDetection(
                    onset_id=token.onset_id,
                    target_id=target_id,
                    probabilities=probabilities,
                    confidence=0.76,
                    detector_id=self.detector_id,
                )
            )

        return tuple(results)
