"""Join timestamp-derived evidence to canonical musical coordinates.

Raw event files remain immutable provenance. Structural sidecars provide the
musical address used for learning/comparison.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from .score_alignment import MusicalScoreCoordinate
from .representation import StructuralPerformanceData, StructuralPerformanceEvent


@dataclass(frozen=True)
class StructuralAlignmentSpan:
    source_id: str
    start_s: float
    end_s: float
    coordinate: MusicalScoreCoordinate
    start_form_bar: int | None = None
    end_form_bar: int | None = None
    alignment_confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.start_s < 0 or self.end_s <= self.start_s:
            raise ValueError("span must satisfy 0 <= start < end")
        if not 0.0 <= self.alignment_confidence <= 1.0:
            raise ValueError("alignment_confidence must be within 0..1")
        self.coordinate.validate()
        if (self.start_form_bar is None) != (self.end_form_bar is None):
            raise ValueError("form-bar range must provide both start and end")
        if self.start_form_bar is not None:
            if self.start_form_bar < 1 or self.end_form_bar < self.start_form_bar:
                raise ValueError("invalid form-bar range")

    def contains(self, time_s: float) -> bool:
        return self.start_s <= time_s < self.end_s

    def locate(self, time_s: float) -> MusicalScoreCoordinate:
        """Return structural location for a timestamp inside this span.

        Bar interpolation is allowed only when an explicit start/end form-bar
        range is supplied by verified alignment. It never invents a range.
        """
        self.validate()
        if not self.contains(time_s):
            raise ValueError("timestamp outside alignment span")

        if self.start_form_bar is None or self.end_form_bar is None:
            return self.coordinate

        bars = self.end_form_bar - self.start_form_bar + 1
        rel = (time_s - self.start_s) / (self.end_s - self.start_s)
        idx = min(bars - 1, max(0, int(rel * bars)))
        form_bar = self.start_form_bar + idx

        section_bar = self.coordinate.section_bar
        if section_bar is None:
            section_bar = idx + 1

        data = dict(self.coordinate.__dict__)
        data["form_bar"] = form_bar
        data["section_bar"] = section_bar
        data["confidence"] = min(
            self.coordinate.confidence,
            self.alignment_confidence,
        )
        return MusicalScoreCoordinate(**data)


class StructuralAlignmentIndex:
    def __init__(self, spans: Iterable[StructuralAlignmentSpan]):
        self._spans = tuple(spans)
        for span in self._spans:
            span.validate()

    def locate(
        self,
        *,
        source_id: str,
        time_s: float,
    ) -> MusicalScoreCoordinate | None:
        matches = [
            span for span in self._spans
            if span.source_id == source_id and span.contains(time_s)
        ]
        if not matches:
            return None
        matches.sort(
            key=lambda span: (
                span.alignment_confidence,
                -(span.end_s - span.start_s),
            ),
            reverse=True,
        )
        return matches[0].locate(time_s)



def align_structural_performance_data(
    data: StructuralPerformanceData,
    index: StructuralAlignmentIndex,
) -> StructuralPerformanceData:
    """Attach canonical musical coordinates to timestamped events.

    Existing coordinates are preserved. Events without onset_seconds remain
    unchanged rather than guessed.
    """
    data.validate()
    aligned_events: list[StructuralPerformanceEvent] = []
    aligned_count = 0
    for event in data.events:
        if event.musical_coordinate is not None:
            aligned_events.append(event)
            aligned_count += 1
            continue
        if event.onset_seconds is None:
            aligned_events.append(event)
            continue
        coordinate = index.locate(source_id=data.source_id, time_s=event.onset_seconds)
        if coordinate is None:
            aligned_events.append(event)
            continue
        aligned_events.append(replace(event, musical_coordinate=coordinate))
        aligned_count += 1

    metadata = dict(data.metadata)
    metadata["structural_alignment_event_count"] = str(aligned_count)
    metadata["structural_alignment_total_event_count"] = str(len(data.events))
    metadata["structural_alignment_status"] = (
        "structure_aligned" if aligned_count else "navigation_only"
    )
    out = replace(data, events=tuple(aligned_events), metadata=metadata)
    out.validate()
    return out
