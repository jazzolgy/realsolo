"""Structure-first canonical musical coordinates.

Wall-clock/audio time is an alignment property, never the primary musical
identity. RealChord is one provider of stable form/section/bar/beat coordinates.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class CanonicalMusicalCoordinate:
    realchord_id: int
    section: str
    measure_in_section: int
    measure_in_form: int
    beat: float
    chorus: int = 0
    occurrence: int = 0

    def validate(self) -> None:
        if self.realchord_id <= 0:
            raise ValueError("realchord_id must be positive")
        if not self.section.strip():
            raise ValueError("section is required")
        if self.measure_in_section < 1 or self.measure_in_form < 1:
            raise ValueError("measure numbers are 1-based")
        if self.beat < 0:
            raise ValueError("beat may not be negative")
        if self.chorus < 0 or self.occurrence < 0:
            raise ValueError("chorus/occurrence may not be negative")


@dataclass(frozen=True)
class AudioCoordinateAlignment:
    coordinate: CanonicalMusicalCoordinate
    onset_sec: float
    duration_sec: float | None = None
    beat_confidence: float = 1.0
    form_confidence: float = 1.0
    provenance: tuple[str,...] = ()

    def validate(self) -> None:
        self.coordinate.validate()
        if self.onset_sec < 0:
            raise ValueError("onset_sec may not be negative")
        if self.duration_sec is not None and self.duration_sec < 0:
            raise ValueError("duration_sec may not be negative")
        for value in (self.beat_confidence,self.form_confidence):
            if not 0.0 <= value <= 1.0:
                raise ValueError("confidence must be within 0..1")
