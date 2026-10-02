"""Partial feature evidence for scanned written bass parts.

Scanned notation often supports rhythm, register, or contour evidence with
different confidence than exact pitch/harmonic-function evidence. Keep those
uncertainties factorized instead of forcing one fully-measured profile.
"""
from __future__ import annotations

from dataclasses import dataclass, fields

from .written_part_comparator import BassLineAbstractProfile


_PROFILE_FEATURES = (
    "root_occupancy_rate",
    "structural_occupancy_rate",
    "scalar_motion_rate",
    "chromatic_approach_rate",
    "enclosure_rate",
    "repeated_pitch_rate",
    "direction_reversal_rate",
    "offbeat_onset_rate",
    "short_subdivision_rate",
    "quarter_floor_coverage",
    "register_center",
    "register_span",
    "register_slope",
)


@dataclass(frozen=True)
class BassFeatureMeasurement:
    feature: str
    value: float
    confidence: float
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.feature not in _PROFILE_FEATURES:
            raise ValueError(f"unknown bass profile feature: {self.feature}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("feature confidence must be within 0..1")


@dataclass(frozen=True)
class PartialBassLineProfile:
    event_count: int | None = None
    measurements: tuple[BassFeatureMeasurement, ...] = ()
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.event_count is not None and self.event_count < 0:
            raise ValueError("event_count cannot be negative")
        seen: set[str] = set()
        for item in self.measurements:
            item.validate()
            if item.feature in seen:
                raise ValueError(f"duplicate feature measurement: {item.feature}")
            seen.add(item.feature)

    def get(self, feature: str) -> BassFeatureMeasurement | None:
        return next((x for x in self.measurements if x.feature == feature), None)


@dataclass(frozen=True)
class PartialBassComparison:
    compared_features: tuple[str, ...]
    weighted_distance: float
    deltas: tuple[tuple[str, float, float], ...]
    # tuple entries are (feature, generated-reference delta, confidence)


def full_profile_as_partial(
    profile: BassLineAbstractProfile,
    *,
    confidence: float = 1.0,
    provenance: tuple[str, ...] = (),
) -> PartialBassLineProfile:
    measurements: list[BassFeatureMeasurement] = []
    for feature in _PROFILE_FEATURES:
        value = getattr(profile, feature)
        if value is None:
            continue
        measurements.append(BassFeatureMeasurement(
            feature,
            float(value),
            confidence,
            provenance,
        ))
    out = PartialBassLineProfile(
        event_count=profile.event_count,
        measurements=tuple(measurements),
        provenance=provenance,
    )
    out.validate()
    return out


def compare_partial_bass_profiles(
    reference: PartialBassLineProfile,
    generated: BassLineAbstractProfile,
) -> PartialBassComparison:
    """Compare only features actually measured in the scanned reference."""
    reference.validate()
    scales = {
        "register_center": 12.0,
        "register_span": 12.0,
        "register_slope": 4.0,
    }
    deltas: list[tuple[str, float, float]] = []
    weighted_error = 0.0
    total_weight = 0.0

    for item in reference.measurements:
        generated_value = getattr(generated, item.feature)
        if generated_value is None:
            continue
        scale = scales.get(item.feature, 1.0)
        delta = float(generated_value) - item.value
        error = min(1.0, abs(delta) / scale)
        weighted_error += error * item.confidence
        total_weight += item.confidence
        deltas.append((item.feature, delta, item.confidence))

    return PartialBassComparison(
        compared_features=tuple(x[0] for x in deltas),
        weighted_distance=weighted_error / max(total_weight, 1e-12),
        deltas=tuple(deltas),
    )
