"""Shared Form Intelligence for every RealSolo player and research process.

This module owns runtime interpretation of musical location. Research Listener,
AI Drummer, piano, bass, sax and later players should consume its state rather
than implement private form tracking.

Physical/source time is retained only as alignment provenance. The musical
learning address is form/section/measure/beat when resolved.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

from music_intelligence.learning.form_position import FormMap, MetricFormPosition


class PerformancePhase(str, Enum):
    UNKNOWN="unknown"
    RUBATO_INTRO="rubato_intro"
    INTRO="intro"
    HEAD="head"
    SOLO="solo"
    INTERLUDE="interlude"
    HEAD_OUT="head_out"
    CODA="coda"
    OUTRO="outro"
    VAMP="vamp"
    TAG="tag"
    ENDING="ending"


@dataclass(frozen=True)
class FormObservation:
    """Evidence entering Shared Form Intelligence.

    absolute_beat is a quarter-note-domain score/performance beat supplied by
    Beat/Meter Intelligence after it has a reliable running beat count. It is
    deliberately optional: unresolved observations must remain unresolved.
    """
    source_time_s: float
    absolute_beat: float | None = None
    meter_numerator: int | None = None
    meter_denominator: int | None = None
    phrase_id: str | None = None
    section_hint: str | None = None
    phase_hint: PerformancePhase = PerformancePhase.UNKNOWN
    arrangement_segment: str | None = None
    arrangement_segment_index: int | None = None
    within_core_form: bool | None = None
    beat_confidence: float = 0.0
    meter_confidence: float = 0.0
    form_confidence: float = 0.0
    boundary_probability: float = 0.0
    provenance: tuple[str,...] = ()

    def validate(self) -> None:
        if self.source_time_s < 0:
            raise ValueError("source_time_s may not be negative")
        if self.absolute_beat is not None and self.absolute_beat < 0:
            raise ValueError("absolute_beat may not be negative")
        for value,name in (
            (self.beat_confidence,"beat_confidence"),
            (self.meter_confidence,"meter_confidence"),
            (self.form_confidence,"form_confidence"),
            (self.boundary_probability,"boundary_probability"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if self.meter_numerator is not None and self.meter_numerator <= 0:
            raise ValueError("meter_numerator must be positive")
        if self.meter_denominator is not None and self.meter_denominator <= 0:
            raise ValueError("meter_denominator must be positive")
        if self.arrangement_segment_index is not None and self.arrangement_segment_index < 0:
            raise ValueError("arrangement_segment_index may not be negative")


@dataclass(frozen=True)
class FormIntelligenceState:
    song_id: str
    source_time_s: float
    position: MetricFormPosition
    performance_phase: PerformancePhase = PerformancePhase.UNKNOWN
    arrangement_segment: str | None = None
    arrangement_segment_index: int | None = None
    within_core_form: bool | None = None
    distance_to_boundary_measures: float | None = None
    boundary_probability: float = 0.0
    confidence: float = 0.0
    provenance: tuple[str,...] = ()

    @property
    def learning_ready(self) -> bool:
        return self.position.resolved_metric

    @property
    def form_ready(self) -> bool:
        return self.position.resolved_form


@dataclass
class SharedFormIntelligence:
    """Causal shared form state.

    A score/corpus FormMap may be attached as expected structure. Runtime beat,
    meter and boundary evidence still determine whether the current location is
    resolved. Metadata never pretends to be performed-audio evidence.
    """
    song_id: str
    expected_form: FormMap | None = None
    expected_form_source_id: str | None = None
    _state: FormIntelligenceState | None = field(default=None,init=False,repr=False)

    def set_expected_form(
        self,
        form_map: FormMap,
        *,
        source_id: str,
    ) -> None:
        form_map.validate()
        if not source_id:
            raise ValueError("expected form source_id is required")
        self.expected_form=form_map
        self.expected_form_source_id=source_id

    def update(self,observation: FormObservation) -> FormIntelligenceState:
        observation.validate()

        if observation.absolute_beat is not None and self.expected_form is not None:
            p=self.expected_form.position_from_absolute_beat(
                observation.absolute_beat,
                phrase_id=observation.phrase_id,
                provenance=(
                    f"expected_form_source:{self.expected_form_source_id or 'unknown'}",
                    "shared_form_intelligence",
                )+observation.provenance,
            )
            # Runtime confidence is bounded by both the corpus/form prior and
            # the observed beat/meter/form evidence.
            runtime=max(
                0.0,
                min(
                    1.0,
                    observation.beat_confidence,
                    max(observation.meter_confidence,.01),
                    max(observation.form_confidence,self.expected_form.confidence*.75),
                ),
            )
            p=replace(p,confidence=min(p.confidence,runtime))
        elif (
            observation.absolute_beat is not None
            and observation.meter_numerator is not None
            and observation.meter_denominator is not None
        ):
            denominator_units=observation.absolute_beat*(observation.meter_denominator/4.0)
            measure=int(denominator_units//observation.meter_numerator)
            beat=denominator_units-measure*observation.meter_numerator
            p=MetricFormPosition(
                measure_index=measure,
                beat_in_measure=beat,
                meter_numerator=observation.meter_numerator,
                meter_denominator=observation.meter_denominator,
                phrase_id=observation.phrase_id,
                absolute_beat=observation.absolute_beat,
                confidence=min(observation.beat_confidence,observation.meter_confidence),
                provenance=observation.provenance+(
                    "shared_form_intelligence:metric_only",
                ),
            )
        else:
            p=MetricFormPosition(
                phrase_id=observation.phrase_id,
                absolute_beat=observation.absolute_beat,
                confidence=0.0,
                provenance=observation.provenance+(
                    "shared_form_intelligence:unresolved",
                ),
            )

        distance=None
        if (
            self.expected_form is not None
            and p.measure_index is not None
        ):
            candidates=[]
            for section in self.expected_form.sections:
                if section.contains(p.measure_index):
                    candidates.append(
                        float(section.start_measure+section.length_measures-p.measure_index-1)
                    )
            if self.expected_form.cycle_measures is not None:
                candidates.append(
                    float(self.expected_form.cycle_measures-p.measure_index-1)
                )
            if candidates:
                distance=max(0.0,min(candidates))

        confidence=max(
            p.confidence,
            observation.boundary_probability*.25 if p.resolved_metric else 0.0,
        )
        state=FormIntelligenceState(
            song_id=self.song_id,
            source_time_s=observation.source_time_s,
            position=p,
            performance_phase=observation.phase_hint,
            arrangement_segment=observation.arrangement_segment,
            arrangement_segment_index=observation.arrangement_segment_index,
            within_core_form=observation.within_core_form,
            distance_to_boundary_measures=distance,
            boundary_probability=observation.boundary_probability,
            confidence=min(1.0,confidence),
            provenance=(
                "shared_music_intelligence:form",
            )+observation.provenance,
        )
        self._state=state
        return state

    @property
    def state(self) -> FormIntelligenceState | None:
        return self._state
