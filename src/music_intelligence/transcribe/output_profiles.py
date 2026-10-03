"""Score-view projections derived from shared logical notation.

This module does not infer harmony or form.  It combines already-authoritative
musical structure with transcription-side notation for product-facing outputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from .chord_chart import ChordChart
from .score import ReadableScore


class OutputProfile(str, Enum):
    LEAD_SHEET = "lead_sheet"
    PIANO_VOCAL = "piano_vocal"
    PIANO_REDUCTION = "piano_reduction"
    FULL_SCORE = "full_score"
    INDIVIDUAL_PART = "individual_part"


@dataclass(frozen=True)
class LeadSheetProjection:
    """A melody score paired with authoritative harmony/form structure."""

    score: ReadableScore
    chart: ChordChart
    melody_part_id: str
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        self.score.validate()
        self.chart.validate()

        if self.score.meter_numerator != self.chart.meter_numerator:
            raise ValueError("lead-sheet score/chart meter numerator mismatch")
        if self.score.meter_denominator != self.chart.meter_denominator:
            raise ValueError("lead-sheet score/chart meter denominator mismatch")

        part_ids = {part.part_id for part in self.score.parts}
        if self.melody_part_id not in part_ids:
            raise ValueError("lead-sheet melody part is missing from score")

        bar_length = Fraction(
            self.score.meter_numerator * 4,
            self.score.meter_denominator,
        )
        melody_part = next(
            part for part in self.score.parts
            if part.part_id == self.melody_part_id
        )
        if melody_part.events:
            last_offset = max(event.span.offset for event in melody_part.events)
            required_measures = int((last_offset + bar_length - Fraction(1, 10**9)) // bar_length)
            required_measures = max(1, required_measures)
            if len(self.chart.measures) < required_measures:
                raise ValueError(
                    "lead-sheet chart does not cover melody score duration"
                )


def project_lead_sheet(
    *,
    score: ReadableScore,
    chart: ChordChart,
    melody_part_id: str,
    provenance: tuple[str, ...] = (),
) -> LeadSheetProjection:
    """Combine melody notation with Core-provided harmony/form information."""

    projection = LeadSheetProjection(
        score=score,
        chart=chart,
        melody_part_id=melody_part_id,
        provenance=provenance + ("transcribe:lead-sheet-projection",),
    )
    projection.validate()
    return projection
