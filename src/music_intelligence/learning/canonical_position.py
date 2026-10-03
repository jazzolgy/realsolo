"""Canonicalize structural learning events into measure/form coordinates."""
from __future__ import annotations

from dataclasses import replace

from .form_position import MetricFormPosition
from .score_alignment import MusicalScoreCoordinate, PerformancePhase
from .canonical_score_bridge import musical_score_coordinate_from_metric_form
from .representation import StructuralPerformanceData, StructuralPerformanceEvent


def parse_meter(meter: str) -> tuple[int,int] | None:
    text=(meter or "").strip()
    if "/" not in text:
        return None
    left,right=text.split("/",1)
    try:
        num,den=int(left),int(right)
    except ValueError:
        return None
    if num<=0 or den<=0:
        return None
    return num,den


def position_from_legacy_beats(
    event: StructuralPerformanceEvent,
    data: StructuralPerformanceData,
) -> MetricFormPosition:
    """Project existing beat-domain events into the canonical musical address.

    This never infers a form section that is not known. If a FormMap exists it
    supplies form/section/iteration. Otherwise a known meter supplies only
    measure + beat. With neither, only absolute beat is retained.
    """
    if event.metric_form_position is not None:
        event.metric_form_position.validate()
        return event.metric_form_position

    if data.form_map is not None:
        return data.form_map.position_from_absolute_beat(
            event.onset_beats,
            phrase_id=event.phrase_id or None,
            provenance=("legacy_onset_beats",),
        )

    parsed=parse_meter(data.meter)
    if parsed is not None:
        numerator,denominator=parsed
        denominator_units=event.onset_beats*(denominator/4.0)
        measure=int(denominator_units//numerator)
        beat=denominator_units-measure*numerator
        out=MetricFormPosition(
            measure_index=measure,
            beat_in_measure=beat,
            meter_numerator=numerator,
            meter_denominator=denominator,
            form_id=data.form_label or None,
            section_id=None,
            section_measure_index=None,
            form_iteration=None,
            phrase_id=event.phrase_id or None,
            absolute_beat=event.onset_beats,
            confidence=min(1.0,event.confidence),
            provenance=("meter_projection","legacy_onset_beats"),
        )
        out.validate()
        return out

    out=MetricFormPosition(
        absolute_beat=event.onset_beats,
        phrase_id=event.phrase_id or None,
        confidence=min(.5,event.confidence),
        provenance=("absolute_beat_only","metric_form_unresolved"),
    )
    out.validate()
    return out


def canonicalize_structural_positions(
    data: StructuralPerformanceData,
) -> StructuralPerformanceData:
    data.validate()
    events=tuple(
        replace(e,metric_form_position=position_from_legacy_beats(e,data))
        for e in data.events
    )
    return replace(
        data,
        events=events,
        provenance=data.provenance+("canonical_metric_form_coordinates",),
    )


def position_feature_map(event: StructuralPerformanceEvent) -> dict[str,object]:
    p=event.metric_form_position
    if p is None:
        return {"metric_form_resolved":False}
    return {
        "metric_form_resolved":p.resolved_metric,
        "measure_index":p.measure_index,
        "measure_number":p.display_measure,
        "beat_in_measure":p.beat_in_measure,
        "beat_number":p.display_beat,
        "meter_numerator":p.meter_numerator,
        "meter_denominator":p.meter_denominator,
        "form_id":p.form_id,
        "section_id":p.section_id,
        "section_measure_index":p.section_measure_index,
        "form_iteration":p.form_iteration,
        "form_path":p.form_path,
        "phrase_id":p.phrase_id,
        "absolute_beat":p.absolute_beat,
        "position_confidence":p.confidence,
    }



def canonical_score_coordinate_for_event(
    event: StructuralPerformanceEvent,
    data: StructuralPerformanceData,
    *,
    song_id: str,
    score_source_id: str = "",
    realchord_id: str = "",
    performance_phase: PerformancePhase = PerformancePhase.UNKNOWN,
) -> MusicalScoreCoordinate:
    """Return the persisted Shared Core coordinate for one listener event.

    MetricFormPosition remains the runtime/form-estimation representation.
    This adapter is the boundary used before persistent learning/comparison.
    """
    metric=position_from_legacy_beats(event,data)
    return musical_score_coordinate_from_metric_form(
        metric,
        song_id=song_id,
        score_source_id=score_source_id,
        realchord_id=realchord_id,
        performance_phase=performance_phase,
        chord_label=event.harmony_label,
        phrase_position=event.phrase_id,
        form_role=data.form_label,
        within_core_form=(True if metric.resolved_form else None),
        provenance=data.provenance+event.provenance+(
            "autonomous_listener_canonical_score_boundary",
        ),
    )
