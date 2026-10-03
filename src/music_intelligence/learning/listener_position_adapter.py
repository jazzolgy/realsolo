"""Adapter from detector/listener form estimates into the one canonical coordinate.

Autonomous listeners may keep their own transient metric/form estimate while
audio is playing. Persisted learning/comparison must cross this adapter into
MusicalScoreCoordinate. No second canonical coordinate is introduced here.
"""
from __future__ import annotations

from typing import Protocol

from .score_alignment import MusicalScoreCoordinate, PerformancePhase


class ListenerFormEstimate(Protocol):
    measure_index: int | None
    beat_in_measure: float | None
    section_id: str | None
    section_measure_index: int | None
    form_iteration: int | None
    confidence: float


def coordinate_from_listener_estimate(
    estimate: ListenerFormEstimate,
    *,
    song_id: str,
    score_source_id: str = "",
    realchord_id: str = "",
    form_length_bars: int | None = None,
    performance_phase: PerformancePhase = PerformancePhase.UNKNOWN,
    arrangement_segment: str = "core_form",
    within_core_form: bool | None = None,
    provenance: tuple[str, ...] = (),
) -> MusicalScoreCoordinate:
    """Convert a runtime detector estimate to Shared Core's persisted address.

    Listener measure_index/section_measure_index are assumed zero-based because
    the existing listener branch uses detector indices. Shared score/form bars
    are one-based. Audio seconds intentionally do not enter this object.
    """
    measure_index=getattr(estimate,"measure_index",None)
    beat=getattr(estimate,"beat_in_measure",None)
    section=getattr(estimate,"section_id",None) or ""
    confidence=float(getattr(estimate,"confidence",0.0))
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("estimate confidence must be within 0..1")

    bar=(measure_index + 1) if measure_index is not None else None
    chorus=getattr(estimate,"form_iteration",None)
    core=within_core_form
    if core is None:
        core=bool(bar is not None and form_length_bars is not None)

    coordinate=MusicalScoreCoordinate(
        song_id=song_id,
        score_source_id=score_source_id,
        realchord_id=realchord_id,
        section=section,
        bar=bar,
        beat=beat,
        form_length_bars=form_length_bars,
        form_bar=bar if core and bar is not None and form_length_bars is not None else None,
        chorus_index=chorus,
        performance_phase=performance_phase,
        arrangement_segment=arrangement_segment,
        within_core_form=core,
        confidence=confidence,
        provenance=provenance+("listener_form_estimate_adapter",),
    )
    coordinate.validate()
    return coordinate
