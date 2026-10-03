"""Canonical metric/form coordinates for RealSolo learning.

Learning and retrieval should reason in musical location (form -> section ->
measure -> beat), not wall-clock seconds. Source seconds remain provenance/evidence
for alignment and re-analysis, but are not the canonical learning address.

Unknown structure is represented explicitly with None. It must not be fabricated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class MetricFormPosition:
    """Musical address of an event.

    measure_index is zero-based internally; display_measure is one-based.
    beat_in_measure is zero-based in meter-denominator units: in 4/4, beat 1 is 0.0 and beat 2 is 1.0; in 6/8, 1.0 means one notated eighth-note unit after the barline. Compound-meter pulse grouping can be modeled separately without losing notation position.
    form_iteration identifies repeated traversals/choruses when known.
    """

    measure_index: int | None = None
    beat_in_measure: float | None = None
    meter_numerator: int | None = None
    meter_denominator: int | None = None
    form_id: str | None = None
    section_id: str | None = None
    section_measure_index: int | None = None
    form_iteration: int | None = None
    form_path: tuple[str,...] = ()
    phrase_id: str | None = None
    absolute_beat: float | None = None
    confidence: float = 0.0
    provenance: tuple[str,...] = ()
    meter_segments: tuple[MeterSegment,...] = ()

    def validate(self) -> None:
        if self.measure_index is not None and self.measure_index < 0:
            raise ValueError("measure_index may not be negative")
        if self.section_measure_index is not None and self.section_measure_index < 0:
            raise ValueError("section_measure_index may not be negative")
        if self.form_iteration is not None and self.form_iteration < 0:
            raise ValueError("form_iteration may not be negative")
        if self.meter_numerator is not None and self.meter_numerator <= 0:
            raise ValueError("meter_numerator must be positive")
        if self.meter_denominator is not None and self.meter_denominator <= 0:
            raise ValueError("meter_denominator must be positive")
        if self.beat_in_measure is not None:
            if self.beat_in_measure < 0:
                raise ValueError("beat_in_measure may not be negative")
            if self.meter_numerator is not None and self.beat_in_measure >= self.meter_numerator:
                raise ValueError("beat_in_measure must fall inside the measure")
        if self.absolute_beat is not None and self.absolute_beat < 0:
            raise ValueError("absolute_beat may not be negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")

    @property
    def display_measure(self) -> int | None:
        return None if self.measure_index is None else self.measure_index + 1

    @property
    def display_beat(self) -> float | None:
        return None if self.beat_in_measure is None else self.beat_in_measure + 1.0

    @property
    def resolved_metric(self) -> bool:
        return self.measure_index is not None and self.beat_in_measure is not None

    @property
    def resolved_form(self) -> bool:
        return self.resolved_metric and self.form_id is not None and self.section_id is not None


@dataclass(frozen=True)
class FormSection:
    section_id: str
    start_measure: int
    length_measures: int
    label: str = ""
    parent_section_id: str | None = None
    section_type: str = ""

    def validate(self) -> None:
        if not self.section_id:
            raise ValueError("section_id is required")
        if self.start_measure < 0:
            raise ValueError("start_measure may not be negative")
        if self.length_measures <= 0:
            raise ValueError("length_measures must be positive")

    def contains(self,measure_index:int) -> bool:
        return self.start_measure <= measure_index < self.start_measure+self.length_measures


@dataclass(frozen=True)
class MeterSegment:
    start_measure: int
    numerator: int
    denominator: int

    def validate(self) -> None:
        if self.start_measure < 0:
            raise ValueError("meter segment start_measure may not be negative")
        if self.numerator <= 0 or self.denominator <= 0:
            raise ValueError("meter segment values must be positive")


@dataclass(frozen=True)
class FormMap:
    form_id: str
    meter_numerator: int
    meter_denominator: int
    sections: tuple[FormSection,...]
    cycle_measures: int | None = None
    style_family: str = ""
    confidence: float = 1.0
    provenance: tuple[str,...] = ()

    def validate(self) -> None:
        if not self.form_id:
            raise ValueError("form_id is required")
        if self.meter_numerator <= 0 or self.meter_denominator <= 0:
            raise ValueError("meter must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        ids=set()
        for section in self.sections:
            section.validate()
            if section.section_id in ids:
                raise ValueError("section_id values must be unique")
            ids.add(section.section_id)
        by_id={s.section_id:s for s in self.sections}
        for section in self.sections:
            if section.parent_section_id is not None and section.parent_section_id not in by_id:
                raise ValueError("parent_section_id must refer to another section")
            seen=set()
            cursor=section
            while cursor.parent_section_id is not None:
                if cursor.section_id in seen:
                    raise ValueError("form section hierarchy may not contain cycles")
                seen.add(cursor.section_id)
                cursor=by_id[cursor.parent_section_id]
        if self.cycle_measures is not None and self.cycle_measures <= 0:
            raise ValueError("cycle_measures must be positive")
        starts=set()
        for seg in self.meter_segments:
            seg.validate()
            if seg.start_measure in starts:
                raise ValueError("meter segment start measures must be unique")
            starts.add(seg.start_measure)
            if self.cycle_measures is not None and seg.start_measure >= self.cycle_measures:
                raise ValueError("cyclic form meter segment must start inside the cycle")

    def meter_at_measure(self, measure_index:int) -> tuple[int,int]:
        if measure_index < 0:
            raise ValueError("measure_index may not be negative")
        active=(self.meter_numerator,self.meter_denominator)
        for seg in sorted(self.meter_segments,key=lambda x:x.start_measure):
            if seg.start_measure <= measure_index:
                active=(seg.numerator,seg.denominator)
            else:
                break
        return active

    def _measure_length_quarter_beats(self, measure_index:int) -> float:
        numerator,denominator=self.meter_at_measure(measure_index)
        return numerator*(4.0/denominator)

    def _locate_absolute_beat(self, absolute_beat:float) -> tuple[int,int|None,float,int,int]:
        """Return local measure, iteration, beat-in-measure, numerator, denominator."""
        if self.cycle_measures is not None:
            cycle_qn=sum(
                self._measure_length_quarter_beats(m)
                for m in range(self.cycle_measures)
            )
            if cycle_qn <= 0:
                raise ValueError("cycle duration must be positive")
            iteration=int(absolute_beat//cycle_qn)
            remaining=absolute_beat-iteration*cycle_qn
            measure=0
            while measure < self.cycle_measures:
                length=self._measure_length_quarter_beats(measure)
                if remaining < length-1e-9:
                    break
                remaining-=length
                measure+=1
            if measure >= self.cycle_measures:
                measure=0
                iteration+=1
                remaining=0.0
        else:
            iteration=None
            remaining=absolute_beat
            measure=0
            # Non-cyclic classical/pop forms may be long; this remains exact and
            # intentionally simple because form maps are normally finite.
            while True:
                length=self._measure_length_quarter_beats(measure)
                if remaining < length-1e-9:
                    break
                remaining-=length
                measure+=1
        numerator,denominator=self.meter_at_measure(measure)
        beat_in_measure=remaining*(denominator/4.0)
        return measure,iteration,beat_in_measure,numerator,denominator

    def position_from_absolute_beat(
        self,
        absolute_beat: float,
        *,
        phrase_id: str | None = None,
        provenance: tuple[str,...] = (),
    ) -> MetricFormPosition:
        self.validate()
        if absolute_beat < 0:
            raise ValueError("absolute_beat may not be negative")
        # Structural onset_beats are quarter-note units. FormMap converts them
        # into the active meter's denominator units, including meter changes.
        measure,iteration,beat,numerator,denominator=self._locate_absolute_beat(absolute_beat)
        containing=[s for s in self.sections if s.contains(measure)]
        section=min(containing,key=lambda s:s.length_measures) if containing else None
        form_path=()
        if section is not None:
            by_id={s.section_id:s for s in self.sections}
            path=[]
            cursor=section
            while True:
                path.append(cursor.section_id)
                if cursor.parent_section_id is None:
                    break
                cursor=by_id[cursor.parent_section_id]
            form_path=tuple(reversed(path))
        return MetricFormPosition(
            measure_index=measure,
            beat_in_measure=beat,
            meter_numerator=numerator,
            meter_denominator=denominator,
            form_id=self.form_id,
            section_id=section.section_id if section else None,
            section_measure_index=(measure-section.start_measure if section else None),
            form_iteration=iteration,
            form_path=form_path,
            phrase_id=phrase_id,
            absolute_beat=absolute_beat,
            confidence=self.confidence,
            provenance=self.provenance+provenance+("form_map_projection",),
        )


@dataclass(frozen=True)
class MetricGridEstimate:
    """Metric position before a full form has been identified."""

    position: MetricFormPosition
    source_time_s: float | None = None
    metadata: Mapping[str,object] = field(default_factory=dict)

    def validate(self) -> None:
        self.position.validate()
        if self.source_time_s is not None and self.source_time_s < 0:
            raise ValueError("source_time_s may not be negative")
